import requests, copy
import os, time, json
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, flash, url_for, jsonify, session, Response
from flask_compress import Compress
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import csv
import tempfile, uuid

_csv_temp_store = {}

_endpoints = {}

def get_endpoints():
    global _endpoints
    if not _endpoints:
        ep_path = os.path.join(os.path.dirname(__file__), 'endpoints.json')
        if os.path.exists(ep_path):
            with open(ep_path, 'r', encoding='utf-8') as f:
                _endpoints = json.load(f)
    return _endpoints

def get_api(key, **kwargs):
    config = get_endpoints()
    base_url = config.get("BASE_URL", "")
    ep = config.get("ENDPOINTS", {}).get(key, {})
    path = ep.get("path", "")
    if kwargs:
        path = path.format(**kwargs)
    url = base_url + path if path.startswith('/') else path
    return url, ep.get("method", "GET"), ep

app = Flask(__name__, static_url_path='/fasihsm-fetcher/static')
Compress(app)  # Enable gzip compression for responses
app.secret_key = 'bebas_aja_yang_penting_aman'
app.config['APPLICATION_ROOT'] = '/fasihsm-fetcher'
app.config['PREFERRED_URL_SCHEME'] = 'http'

STATE_FILE    = '.session_state.json'
SESSION_CACHE = '.session_cache.json'
STOP_FLAGS_FILE = '.stop_flags.json'

def set_stop_flag(period_id, value):
    flags = {}
    if os.path.exists(STOP_FLAGS_FILE):
        try:
            with open(STOP_FLAGS_FILE, 'r') as f:
                flags = json.load(f)
        except:
            pass
    flags[period_id] = value
    with open(STOP_FLAGS_FILE, 'w') as f:
        json.dump(flags, f)

def get_stop_flag(period_id):
    if os.path.exists(STOP_FLAGS_FILE):
        try:
            with open(STOP_FLAGS_FILE, 'r') as f:
                flags = json.load(f)
                return flags.get(period_id, False)
        except:
            return False
    return False


# ── Session State Persistence ─────────────────────────────────────────────────

def save_state(is_running: bool):
    with open(STATE_FILE, 'w') as f:
        json.dump({'is_running': is_running}, f)

def load_state() -> bool:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                return json.load(f).get('is_running', False)
        except:
            return False
    return False

def check_session() -> bool:
    return load_state()

def save_session_cache(cookies: list, csrf: str, user_agent: str, id_token: str = ""):
    with open(SESSION_CACHE, 'w') as f:
        json.dump({'cookies': cookies, 'csrf': csrf, 'user_agent': user_agent, 'id_token': id_token}, f)

def load_session_cache() -> dict:
    if os.path.exists(SESSION_CACHE):
        try:
            with open(SESSION_CACHE) as f:
                return json.load(f)
        except:
            pass
    return {}

def clear_session_cache():
    for f in [STATE_FILE, SESSION_CACHE]:
        if os.path.exists(f):
            os.remove(f)


# ── Global pending OTP ────────────────────────────────────────────────────────
_login_pending = {}  # simpan session requests + form OTP sementara


def login_fasih_requests(user, pwd):
    UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/145.0.0.0 Safari/537.36"
    s = requests.Session()
    s.headers.update({
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })

    url_login_page, _, _ = get_api("LOGIN_PAGE")
    s.get(url_login_page, timeout=15, allow_redirects=True)
    
    url_login_auth, _, _ = get_api("LOGIN_AUTH")
    r_kc = s.get(url_login_auth, timeout=15, allow_redirects=True)

    soup = BeautifulSoup(r_kc.text, 'html.parser')
    form = soup.find('form')
    if not form:
        raise Exception("Form login Keycloak tidak ditemukan. Cek koneksi/VPN.")
    action_url = form.get('action')
    if not action_url:
        raise Exception("Action URL form Keycloak tidak ditemukan.")

    r_login = s.post(action_url, data={"username": user, "password": pwd},
                     timeout=15, allow_redirects=True)

    # Cek apakah muncul form OTP
    soup2 = BeautifulSoup(r_login.text, 'html.parser')
    otp_input = soup2.find('input', {'name': 'otp'}) or soup2.find('input', {'id': 'otp'})

    if otp_input:
        form2 = soup2.find('form')
        otp_data = {
            inp.get('name'): inp.get('value', '')
            for inp in form2.find_all('input') if inp.get('name')
        }
        otp_data.pop('cancel', None)
        _login_pending['session']    = s
        _login_pending['otp_action'] = form2.get('action')
        _login_pending['otp_data']   = otp_data
        return {"needs_otp": True}

    if "fasih-sm.bps.go.id" not in r_login.url:
        raise Exception("Login gagal. Cek username/password atau akses VPN BPS.")

    _finalize_login(s, UA)
    return {"needs_otp": False}

def _finalize_login(s: requests.Session, ua: str):
    csrf    = s.cookies.get("XSRF-TOKEN", "")
    cookies = [{"name": c.name, "value": c.value} for c in s.cookies]
    
    # Coba ambil ID token dari cookies
    id_token = ""
    for c in s.cookies:
        if "id_token" in c.name.lower() or "token" in c.name.lower():
            id_token = c.value
            break
    
    save_session_cache(cookies, csrf, ua, id_token)
    save_state(True)

# ── Helpers ───────────────────────────────────────────────────────────────────

def format_fasih_date(date_str, timezone_label="WITA"):
    if not date_str or date_str == "-":
        return "-"
    tz_offset = {"WIB": 7, "WITA": 8, "WIT": 9}
    offset = tz_offset.get(timezone_label, 8)
    try:
        clean_date = date_str.split(".")[0]
        if "T" not in clean_date:
            return date_str
        dt = datetime.strptime(clean_date, "%Y-%m-%dT%H:%M:%S")
        dt_local = dt + timedelta(hours=offset)
        return dt_local.strftime(f"%d %b %Y at %H.%M {timezone_label}")
    except:
        try:
            return f"{date_str[:10]} (Raw)"
        except:
            return date_str

def get_req_session():
    cache = load_session_cache()
    req_session = requests.Session()
    if not cache:
        return req_session
    for cookie in cache.get('cookies', []):
        req_session.cookies.set(cookie['name'], cookie['value'])
    req_session.headers.update({
        "User-Agent":   cache.get('user_agent', ''),
        "Accept":       "application/json, text/plain, */*",
        "X-XSRF-TOKEN": cache.get('csrf', ''),
    })
    return req_session

def fetch_list_surveys(req_session, survey_type="Pencacahan", page_size=100):
    url, meth, ep = get_api("LIST_SURVEYS")
    url = f"{url}?surveyType={survey_type}"
    payload = ep.get("default_payload", {}).copy()
    payload["pageSize"] = page_size
    try:
        response = req_session.request(meth, url, json=payload, timeout=15)
        if response.status_code == 200:
            return response.json().get('data', {}).get('content', [])
    except Exception as e:
        print(f"[fetch_list_surveys] Error: {e}")
    return []

def fetch_json(req_session, url):
    try:
        r = req_session.get(url, timeout=30)
        r.raise_for_status()
        res = r.json()
        return res.get("data") if res.get("data") is not None else {}
    except Exception as e:
        print(f"[fetch_json] Error {url}: {e}")
        return {}


# ── Metadata Survei ───────────────────────────────────────────────────────────

def fetch_full_survey_settings_flat(req_session, survey_id):
    with ThreadPoolExecutor(max_workers=2) as executor:
        url_det, _, _ = get_api("SURVEY_DETAIL", survey_id=survey_id)
        url_per, _, _ = get_api("SURVEY_PERIODS", survey_id=survey_id)
        f_det = executor.submit(fetch_json, req_session, url_det)
        f_per = executor.submit(fetch_json, req_session, url_per)
        det = f_det.result()
        per = f_per.result()

    per_list  = per if isinstance(per, list) else []
    region_id = det.get("regionGroupId")
    url_reg, _, _ = get_api("REGION_METADATA", region_id=region_id)
    reg       = fetch_json(req_session, url_reg) if region_id else {}
    act_per   = next((p for p in per_list if p.get("isActive")), per_list[0] if per_list else {})

    # Dynamic regional context detection
    level2_id = None
    level2_code = None
    level1_code = None
    
    if act_per.get("id"):
        try:
            # Source 1: User's info (Very reliable for jurisdiction)
            # Try fetching with period_id first, then without to get cross-period jurisdiction
            url_my_base, meth_my, _ = get_api("REGION_MYINFO")
            url_my = f"{url_my_base}?surveyPeriodId={act_per.get('id')}" if act_per.get("id") else url_my_base
            my_info = fetch_json(req_session, url_my)
            
            d_my = {}
            if my_info:
                if my_info.get("success"):
                    d_my = my_info.get("data", {})
                else:
                    d_my = my_info
            
            # If no regionId in current period, try fetching WITHOUT period to get all allocations
            if not d_my.get("regionId") and not d_my.get("allocations"):
                my_info_all = fetch_json(req_session, url_my_base)
                if my_info_all:
                    if my_info_all.get("success"): d_my = my_info_all.get("data", {})
                    else: d_my = my_info_all
            
            if d_my:
                # regionId or parentRegionCode usually contains the Kabupaten code (e.g. "6309")
                r_codes = d_my.get("regionId") or []
                if not r_codes and d_my.get("allocations"):
                    # Look for ANY parentRegionCode in allocations
                    r_codes = list(set([a.get("parentRegionCode") for a in d_my.get("allocations") if a.get("parentRegionCode")]))
                
                print(f"[Regional Detection] Found r_codes: {r_codes}")
                
                if r_codes:
                    level2_code = str(r_codes[0])
                    level1_code = level2_code[:2]
                    
                    # Now fetch the Kabupaten ID (level2_id) from the code
                    url_l2, meth_l2, _ = get_api("REGION_LEVEL2")
                    full_url_l2 = f"{url_l2}?groupId={region_id}&level1FullCode={level1_code}"
                    res_l2 = req_session.request(meth_l2, full_url_l2)
                    if res_l2.status_code == 200:
                        l2_data = res_l2.json().get("data", [])
                        matching = next((x for x in l2_data if x.get("fullCode") == level2_code), None)
                        if matching:
                            level2_id = matching.get("id")
                            print(f"[Regional Detection] Matched level2_id: {level2_id}")
            else:
                print(f"[Regional Detection] MyInfo failed or empty: {my_info}")

            # Source 2: Fallback to peek 1 sample if Source 1 failed
            if not level2_id and not level2_code:
                url_s, meth_s, ep_s = get_api("SAMPEL_DATATABLE")
                payload = copy.deepcopy(ep_s.get("default_payload", {}))
                payload["assignmentExtraParam"]["surveyPeriodId"] = act_per.get("id")
                payload["length"] = 1
                res_s = req_session.request(meth_s, url_s, json=payload, timeout=10)
                if res_s.status_code == 200:
                    data_s = res_s.json().get("searchData", [])
                    if data_s:
                        reg_info = data_s[0].get("region", {})
                        lvl1 = reg_info.get("level1", {})
                        lvl2 = lvl1.get("level2", {})
                        level1_code = lvl1.get("code")
                        level2_id = lvl2.get("id")
                        level2_code = lvl2.get("fullCode")
        except Exception as e:
            print(f"[fetch_full_survey_settings_flat] Regional context detection error: {e}")

    return {
        "judul":          det.get("name", "-"),
        "tipe":           det.get("surveyType", "-"),
        "mode":           ", ".join([m.get("mode", "") for m in det.get("surveyModeList", [])]) if det.get("surveyModeList") else "-",
        "wilayah_ver":    reg.get("groupName", "-"),
        "level_wilayah":  " > ".join([l.get("name", "") for l in reg.get("level", [])]) if reg.get("level") else "-",
        "jenis_panel":    "Panel" if det.get("panelType") else "Non-Panel",
        "jenis_pencacah": "Banyak" if det.get("isMultiPencacah") else "Satu",
        "periode_aktif":  act_per.get("name", "-"),
        "tgl_mulai":      format_fasih_date(act_per.get("startDate"), timezone_label="WITA"),
        "tgl_selesai":    format_fasih_date(act_per.get("endDate"), timezone_label="WITA"),
        "id_periode":     act_per.get("id", "-"),
        "group_id":       region_id,
        "level2_id":      level2_id,
        "level2_code":    level2_code,
        "level1_code":    level1_code,
        "periods":        per_list
    }


# ── Petugas ───────────────────────────────────────────────────────────────────

def fetch_petugas_all_roles(req_session, survey_id, period_id):
    role_url, role_meth, _ = get_api("SURVEY_ROLES", survey_id=survey_id)
    try:
        role_res   = req_session.request(role_meth, role_url, timeout=15)
        roles_data = role_res.json().get("data", []) if role_res.status_code == 200 else []
    except:
        return {"roles": [], "data": {}}

    def fetch_by_role(role):
        role_id  = role.get("id")
        api_url, api_meth, ep = get_api("FETCH_PETUGAS")
        params = ep.get("default_params", {}).copy()
        params["surveyRoleId"] = role_id
        params["surveyPeriodId"] = period_id

        try:
            res = req_session.request(api_meth, api_url, params=params, timeout=15)
            if res.status_code != 200:
                print(f"[fetch_by_role] HTTP {res.status_code} for {role_id}")
                print(f"[fetch_by_role] URL: {res.url}")
                print(f"[fetch_by_role] Response: {res.text}")
                return []
            
            raw_data = res.json().get("data")
            if not raw_data:
                return []
                
            rows = []
            for i, item in enumerate(raw_data.get("content", []), start=1):
                raw_regions = item.get("regions") or []
                regions = [r.get("regionCode") for r in raw_regions if r.get("regionCode")]
                rows.append({
                    "no":      i,
                    "nama":    item.get("username") or "-",
                    "email":   item.get("email") or "-",
                    "wilayah": ", ".join([str(r) for r in regions]) if regions else "-",
                })
            return rows
        except Exception as e:
            print(f"[fetch_by_role] Exception for {role_id}: {e}")
            return []

    roles_meta = []
    data = {}
    with ThreadPoolExecutor(max_workers=len(roles_data) or 1) as executor:
        futures = {}
        for role in roles_data:
            desc = role.get("description", "")
            key  = desc.lower().replace(" ", "_")
            roles_meta.append({"key": key, "label": desc})
            futures[key] = executor.submit(fetch_by_role, role)
        for key, future in futures.items():
            data[key] = future.result()

    return {"roles": roles_meta, "data": data}


# ── Ringkasan Sampel ──────────────────────────────────────────────────────────

def fetch_sampel_aggregation(req_session, period_id):
    url, meth, ep = get_api("SAMPEL_DATATABLE")
    import copy
    payload = copy.deepcopy(ep.get("default_payload", {}))
    extra = {
        **{f"region{i}Id": None for i in range(1, 11)},
        "surveyPeriodId":         period_id,
        "assignmentErrorStatusType": -1,
        "assignmentStatusAlias":  None,
        **{f"data{i}": None for i in range(1, 11)},
        "userIdResponsibility": None, "currentUserId": None, "regionId": None
    }
    payload["assignmentExtraParam"].update(extra)
    try:
        res = req_session.request(meth, url, json=payload, timeout=15)
        if res.status_code == 200:
            data = res.json()
            return {"total": data.get("totalHit", 0), "statuses": data.get("searchAggregation", [])}
    except Exception as e:
        print(f"[fetch_sampel_aggregation] {e}")
    return {"total": 0, "statuses": []}

def _fetch_sampel_generator(req_session, period_id, filters, tz="WITA"):
    url, meth, ep = get_api("SAMPEL_DATATABLE")
    all_rows   = []
    start_idx  = 0
    draw_count = 1
    batch_size = 50
    total_hit  = 1 # dummy initial
    
    CHUNK_LIMIT = 1000

    while start_idx < total_hit:
        chunk_target = min(start_idx + CHUNK_LIMIT, total_hit) if total_hit > 1 else CHUNK_LIMIT
        
        while start_idx < chunk_target:
            import copy
            payload = copy.deepcopy(ep.get("default_payload", {}))
            payload["draw"] = draw_count
            payload["start"] = start_idx
            payload["length"] = batch_size
            extra = {
                **{f"region{i}Id": None for i in range(1, 11)},
                "surveyPeriodId":         period_id,
                "assignmentErrorStatusType": -1,
                "assignmentStatusAlias":  filters.get("status_alias") if filters.get("status_alias") != "SEMUA" else None,
                **{f"data{i}": None for i in range(1, 11)},
                "userIdResponsibility": filters.get("user_id"),
                "currentUserId":        filters.get("user_id"),
                "userId":               filters.get("user_id"),
                "regionId":             None
            }
            if filters.get("region3Id"): extra["region3Id"] = filters.get("region3Id")
            if filters.get("region4Id"): extra["region4Id"] = filters.get("region4Id")
            
            payload["assignmentExtraParam"].update(extra)
            print(f"[_fetch_sampel_generator] Fetching start={start_idx}, payload: {json.dumps(payload)}")
            try:
                res = req_session.request(meth, url, json=payload, timeout=30)
                if res.status_code != 200:
                    start_idx = total_hit
                    break
                raw = res.json()
                
                total_hit = raw.get("totalHit", 0)
                if total_hit == 0:
                    start_idx = total_hit + 1 # Force break
                    break
                    
                if total_hit > 0 and start_idx == 0: # Update total hit on first success
                    current_total = total_hit
                
                chunk_target = min(chunk_target, total_hit) if chunk_target == CHUNK_LIMIT else chunk_target
                
                search_data = raw.get("searchData", [])
                for item in search_data:
                    reg  = item.get("region", {})
                    lvl3 = reg.get("level1", {}).get("level2", {}).get("level3", {}) or {}
                    lvl4 = lvl3.get("level4", {}) or {}
                    lvl5 = lvl4.get("level5", {}) or {}
                    lvl6 = lvl5.get("level6", {}) or {}
                    all_rows.append({
                        "no":         len(all_rows) + 1,
                        "id_sls":     item.get("codeIdentity", "-"),
                        "kk":         item.get("data1") or "-",
                        "anggota":    item.get("data2") or "-",
                        "alamat":     item.get("data3") or "-",
                        "status_kb":  item.get("data4") or "-",
                        "status_dok": item.get("assignmentStatusAlias", "-"),
                        "pencacah":   item.get("currentUserFullname") or "-",
                        "email_pcj":  item.get("currentUserUsername") or "-",
                        "kec":        f"{lvl3.get('code','-')}. {lvl3.get('name','-')}" if lvl3 else "-",
                        "des":        f"{lvl4.get('code','-')}. {lvl4.get('name','-')}" if lvl4 else "-",
                        "sls":        lvl5.get("name", "-") if lvl5 else "-",
                        "sub_sls":    lvl6.get("code", "-") if lvl6 else "-",
                        "modified":   format_fasih_date(item.get("dateModified"), timezone_label=tz),
                        "sample_id":  item.get("id", "-"),
                        "lat":        item.get("latitude", 0),
                        "lon":        item.get("longitude", 0),
                        "created":    format_fasih_date(item.get("dateCreated"), timezone_label=tz),
                    })
                start_idx += batch_size
                draw_count += 1
                yield {"type": "progress", "progress": min(start_idx, total_hit), "total": total_hit}
                time.sleep(0.01)
                
                if len(search_data) < batch_size:
                    start_idx = total_hit
                    break
            except Exception as e:
                print(f"[_fetch_sampel_generator] Chunk Error: {e}")
                start_idx = total_hit
                break
                
        if start_idx < total_hit:
            time.sleep(1)
            
    yield {"type": "done", "rows": all_rows}


# ── Download Sampel ───────────────────────────────────────────────────────────

@app.route('/api/sampel-detail-csv', methods=['POST'])
def api_sampel_detail_csv():
    if not check_session():
        return jsonify({"error": "Sesi tidak aktif"}), 401
    body        = request.get_json()
    sample_ids  = body.get("sample_ids", [])
    survey_name = body.get("survey_name", "rincian_sampel")
    if not sample_ids:
        return jsonify({"error": "sample_ids kosong"}), 400
    req_session = get_req_session()
    total       = len(sample_ids)

    def generate():
        all_rows = []
        
        def fetch_detail(s_id):
            url, meth, _ = get_api("SAMPEL_DETAIL", s_id=s_id)
            try:
                res = req_session.request(meth, url, timeout=15)
                if res.status_code == 200:
                    row = parse_detail_sample(res.json())
                    return row if row else None
            except Exception as e:
                print(f"[detail-csv] ERROR {s_id}: {e}")
            return None
        
        # Fetch all samples in parallel (max 5 concurrent requests)
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(fetch_detail, s_id): (i+1, s_id) for i, s_id in enumerate(sample_ids)}
            completed = 0
            for future in futures:
                try:
                    row = future.result()
                    if row:
                        all_rows.append(row)
                except Exception as e:
                    print(f"[detail-csv] Fetch error: {e}")
                completed += 1
                yield f'data: {{"progress": {completed}, "total": {total}}}\n\n'

        if all_rows:
            all_keys = []
            seen = set()
            for row in all_rows:
                for k in row.keys():
                    if k not in seen:
                        all_keys.append(k)
                        seen.add(k)
            token = str(uuid.uuid4())
            tmp   = tempfile.NamedTemporaryFile(delete=False, suffix='.csv', mode='w',
                                                encoding='utf-8-sig', newline='')
            writer = csv.DictWriter(tmp, fieldnames=all_keys, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(all_rows)
            tmp.close()
            safe_name = survey_name.replace('"', '').replace('/', '-')
            _csv_temp_store[token] = {"path": tmp.name, "filename": f"{safe_name}.csv"}
            yield f'data: {{"done": true, "token": "{token}", "filename": "{safe_name}.csv"}}\n\n'
        else:
            yield f'data: {{"done": true, "error": "Tidak ada data berhasil diambil"}}\n\n'

    return Response(generate(), mimetype='text/event-stream',
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

@app.route('/api/sampel-detail-download/<token>')
def api_sampel_detail_download(token):
    entry = _csv_temp_store.pop(token, None)
    if not entry or not os.path.exists(entry["path"]):
        return "File tidak ditemukan atau sudah diunduh.", 404
    def stream_and_delete():
        try:
            with open(entry["path"], 'rb') as f:
                yield from f
        finally:
            os.remove(entry["path"])
    return Response(stream_and_delete(), mimetype='text/csv',
                    headers={"Content-Disposition": f'attachment; filename="{entry["filename"]}"'})

def parse_detail_sample(json_response):
    if not json_response or not json_response.get("success"):
        return None
    raw_data = json_response.get("data", {})
    result = {
        "Sample ID":        raw_data.get("_id"),
        "ID SLS":           raw_data.get("code_identity"),
        "Status Dokumen":   raw_data.get("assignment_status_alias"),
        "Latitude":         raw_data.get("latitude"),
        "Longitude":        raw_data.get("longitude"),
        "Petugas Terakhir": raw_data.get("current_user_fullname"),
    }
    try:
        pre_data = json.loads(raw_data.get("pre_defined_data", "{}"))
        for item in pre_data.get("predata", []):
            val = item.get("answer")
            result[f"Prelist_{item.get('dataKey')}"] = str(val) if not isinstance(val, (list, dict)) else json.dumps(val, ensure_ascii=False)
    except:
        pass
    try:
        content_data = json.loads(raw_data.get("data", "{}"))
        result["Waktu Submit"] = content_data.get("updatedAt")
        for ans in content_data.get("answers", []):
            val = ans.get("answer")
            if isinstance(val, list):
                result[f"Ans_{ans.get('dataKey')}"] = ", ".join(
                    [str(v.get('label', v)) if isinstance(v, dict) else str(v) for v in val])
            else:
                result[f"Ans_{ans.get('dataKey')}"] = val
    except:
        pass
    return result


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route('/')
def home():
    user = session.get('fasih_user') or os.getenv("FASIH_USER")
    return render_template('index.html', is_running=load_state(), user=user)

@app.route('/import-env', methods=['POST'])
def import_env():
    load_dotenv(override=True)
    user = os.getenv("FASIH_USER")
    pwd  = os.getenv("FASIH_PASS")
    if user is None or pwd is None:
        flash('Warning: File .env tidak ditemukan!', 'danger')
    elif not user.strip() or not pwd.strip():
        flash('Isian .env nya salah (kosong)!', 'warning')
    else:
        session['fasih_user'] = user
        flash('Berhasil impor.', 'success')
    return redirect(url_for('home'))

@app.route('/import-env', methods=['GET'])
def import_env_get():
    flash(f"Path {request.path} tidak bisa diakses langsung.", "danger")
    return redirect(url_for('home'))

# login
@app.route('/login')
def login():
    if load_state():
        flash("Sesi masih aktif!", "warning")
        return redirect(url_for('home'))
    user = os.getenv("FASIH_USER")
    pwd  = os.getenv("FASIH_PASS")
    if not user or not pwd:
        flash("Gagal: Variabel belum diimpor! Klik 'Import .env' dulu.", "danger")
        return redirect(url_for('home'))
    try:
        result = login_fasih_requests(user, pwd)
        if result.get("needs_otp"):
            session['needs_otp'] = True
            flash("Masukkan kode OTP dari aplikasi authenticator.", "info")
        else:
            flash("Login sukses. Sesi aktif.", "success")
    except Exception as e:
        save_state(False)
        clear_session_cache()
        flash(f"Login gagal: {str(e)}", "danger")
    return redirect(url_for('home'))

# login with otp
@app.route('/login-otp', methods=['POST'])
def login_otp():
    if 'session' not in _login_pending:
        flash("Tidak ada sesi login pending. Coba login ulang.", "danger")
        return redirect(url_for('home'))

    otp_code = request.form.get('otp', '').strip()
    if not otp_code:
        flash("Kode OTP tidak boleh kosong.", "warning")
        return redirect(url_for('home'))

    s          = _login_pending['session']
    otp_action = _login_pending['otp_action']
    otp_data   = _login_pending['otp_data'].copy()
    otp_data['otp'] = otp_code

    UA = s.headers.get("User-Agent", "")
    try:
        r2 = s.post(otp_action, data=otp_data, timeout=15, allow_redirects=True)
        if 'fasih-sm.bps.go.id' in r2.url:
            _finalize_login(s, UA)
            _login_pending.clear()
            session.pop('needs_otp', None)
            flash("Login sukses. Sesi aktif.", "success")
        else:
            soup3    = BeautifulSoup(r2.text, 'html.parser')
            err      = soup3.find(class_='kc-feedback-text') or soup3.find(class_='alert-error')
            msg      = err.get_text(strip=True) if err else "OTP salah atau expired."
            flash(f"OTP gagal: {msg}", "danger")
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")

    return redirect(url_for('home'))

# logout
@app.route('/logout')
def logout():
    cache = load_session_cache()
    
    # Step 1: POST app logout endpoint
    if cache.get('csrf'):
        try:
            s = requests.Session()
            for cookie in cache.get('cookies', []):
                s.cookies.set(cookie['name'], cookie['value'])
            url_logout, meth_logout, _ = get_api("LOGOUT")
            s.request(meth_logout, url_logout, 
                   data={'_csrf': cache.get('csrf')}, 
                   timeout=10, allow_redirects=False)
        except Exception as e:
            print(f"[logout] POST app endpoint error: {e}")
    
    # Step 2: GET SSO logout endpoint (if ID token available)
    id_token = cache.get('id_token', '')
    if id_token:
        try:
            sso_base = get_endpoints().get("SSO_LOGOUT_URL", "")
            sso_logout_url = (
                f"{sso_base}?id_token_hint={id_token}"
                f"&post_logout_redirect_uri=http://ui-management-ics.apps.kube.bps.go.id"
            )
            requests.get(sso_logout_url, timeout=10, allow_redirects=True)
        except Exception as e:
            print(f"[logout] GET SSO endpoint error: {e}")
    
    # Step 3: Clear local session
    save_state(False)
    clear_session_cache()
    
    flash("Logout berhasil.", "info")
    return redirect(url_for('home'))

@app.route('/secret-wipe')
def secret_wipe():
    for key in ["FASIH_USER", "FASIH_PASS"]:
        os.environ.pop(key, None)
    session.pop('fasih_user', None)  # ← tambah ini
    flash("Variabel dihapus!", "warning")
    return redirect(url_for('home'))

@app.route('/listsurvei')
@app.route('/listsurvei/<category>')
@app.route('/listsurvei/<category>/<survey_id>')
def listsurvei(category="Pencacahan", survey_id=None):
    if not check_session():
        flash("Login terlebih dahulu.", "danger")
        return redirect(url_for('home'))
    req_session = get_req_session()
    raw = fetch_list_surveys(req_session, survey_type=category)
    surveys = []
    for i, item in enumerate(raw, start=1):
        surveys.append({
            "no":           i,
            "judul_survei": item.get("name", "-"),
            "id":           item.get("id", "-"),
            "unit":         item.get("unit", "-"),
            "dibuat_pada":  format_fasih_date(item.get("createdAt"), timezone_label="WITA")
        })
    meta    = None
    petugas = []
    if survey_id:
        meta = fetch_full_survey_settings_flat(req_session, survey_id)
        req_period = request.args.get("period_id")
        if req_period:
            meta["id_periode"] = req_period
            for p in meta.get("periods", []):
                if p.get("id") == req_period:
                    meta["periode_aktif"] = p.get("name")
                    break
                    
        if meta and meta.get("id_periode") and meta["id_periode"] != "-":
            petugas = fetch_petugas_all_roles(req_session, survey_id, meta["id_periode"])
    return render_template('listsurvei.html', surveys=surveys, active_cat=category,
                           meta=meta, selected_id=survey_id, petugas=petugas)

@app.route('/api/sampel-status')
def api_sampel_status():
    if not check_session():
        return jsonify({"error": "Sesi tidak aktif"}), 401
    period_id = request.args.get("period_id", "")
    if not period_id:
        return jsonify({"error": "period_id diperlukan"}), 400
    return jsonify(fetch_sampel_aggregation(get_req_session(), period_id))

@app.route('/api/sampel-fetch', methods=['POST'])
def api_sampel_fetch():
    if not check_session():
        return jsonify({"error": "Sesi tidak aktif"}), 401
    body         = request.get_json()
    period_id    = body.get("period_id", "")
    filters      = body.get("filters", {})
    tz           = body.get("tz", "WITA")
    if not period_id:
        return jsonify({"error": "period_id diperlukan"}), 400
        
    req_session = get_req_session()
    
    def generate():
        for msg in _fetch_sampel_generator(req_session, period_id, filters, tz):
            if msg["type"] == "progress":
                yield f'data: {json.dumps({"progress": msg["progress"], "total": msg["total"]})}\n\n'
            elif msg["type"] == "done":
                yield f'data: {json.dumps({"done": True, "rows": msg["rows"]})}\n\n'

    return Response(generate(), mimetype='text/event-stream', headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

@app.route('/api/proxy/region/level3')
def proxy_region_level3():
    if not check_session(): return jsonify({"error": "Sesi tidak aktif"}), 401
    group_id = request.args.get("groupId")
    level2_id = request.args.get("level2Id")
    if not group_id or not level2_id: return jsonify({"data": []})
    url, meth, _ = get_api("REGION_LEVEL3")
    res = get_req_session().request(meth, f"{url}?groupId={group_id}&level2Id={level2_id}")
    return jsonify(res.json() if res.status_code == 200 else {"data": []})

@app.route('/api/proxy/region/level4')
def proxy_region_level4():
    if not check_session(): return jsonify({"error": "Sesi tidak aktif"}), 401
    group_id = request.args.get("groupId")
    level3_id = request.args.get("level3Id")
    if not group_id or not level3_id: return jsonify({"data": []})
    url, meth, _ = get_api("REGION_LEVEL4")
    res = get_req_session().request(meth, f"{url}?groupId={group_id}&level3Id={level3_id}")
    return jsonify(res.json() if res.status_code == 200 else {"data": []})

@app.route('/api/proxy/users')
def proxy_users():
    if not check_session(): return jsonify({"error": "Sesi tidak aktif"}), 401
    period_id = request.args.get("surveyPeriodId")
    survey_id = request.args.get("surveyId")
    role_id   = request.args.get("surveyRoleId")
    region_code = request.args.get("regionCode")
    
    req_session = get_req_session()
    
    if not role_id and survey_id:
        try:
            role_url, role_meth, _ = get_api("SURVEY_ROLES", survey_id=survey_id)
            r_res = req_session.request(role_meth, role_url, timeout=10)
            if r_res.status_code == 200:
                roles = r_res.json().get("data", [])
                p_role = next((r for r in roles if r.get("isPencacah") or "pencacah" in r.get("name", "").lower()), None)
                if p_role:
                    role_id = p_role.get("id")
        except Exception as e:
            print(f"[proxy_users] Role detection error: {e}")

    if not period_id or not role_id:
        return jsonify({"data": []})

    url, meth, _ = get_api("REGION_USERS")
    params = f"?surveyPeriodId={period_id}&surveyRoleId={role_id}"
    if region_code and region_code != "None":
        params += f"&regionCode={region_code}"
        
    res = req_session.request(meth, f"{url}{params}")
    return jsonify(res.json() if res.status_code == 200 else {"data": []})

@app.errorhandler(404)
def page_not_found(e):
    flash(f"Path {request.path} tidak ada.", "danger")
    return redirect(url_for('home'))

@app.errorhandler(405)
def method_not_allowed(e):
    flash(f"Path {request.path} tidak bisa diakses dengan method ini.", "danger")
    return redirect(url_for('home'))

# ── buat bulk approve ───────────────────────────────────────────────────────────────────────
@app.route('/api/auto-approve', methods=['POST'])
def api_auto_approve():
    if not check_session():
        return jsonify({"error": "Sesi tidak aktif"}), 401

    body = request.get_json()
    period_id = body.get("period_id", "")
    n_target = int(body.get("n_target", 100))
    tz = body.get("tz", "WITA")

    if not period_id:
        return jsonify({"error": "period_id diperlukan"}), 400

    set_stop_flag(period_id, False)
    req_session = get_req_session()

    fetch_limit = max(n_target * 3, 300)
    rows = fetch_sampel_by_status(
        req_session=req_session,
        period_id=period_id,
        n_target=fetch_limit,
        batch_size=100,
        status_alias="SUBMITTED BY Pencacah",
        tz="WITA"
    )

    rows_submitted = [r for r in rows if r.get("status_dok") == "SUBMITTED BY Pencacah"]
    assignment_ids = [r.get("sample_id") for r in rows_submitted if r.get("sample_id")][:n_target]
    total = len(assignment_ids)

    def generate():
        if total == 0:
            yield 'data: {"done": true, "error": "Tidak ada assignment SUBMITTED BY Pencacah yang ditemukan"}\n\n'
            return

        success_count = 0
        failed = []

        for i, assignment_id in enumerate(assignment_ids, start=1):
            if get_stop_flag(period_id):
                yield f'data: {json.dumps({
                    "done": True,
                    "stopped": True,
                    "total": total,
                    "success": success_count,
                    "failed_count": len(failed),
                    "first_error": failed[0] if failed else None
                })}\n\n'
                set_stop_flag(period_id, False)
                return
            result = approve_assignment(req_session, assignment_id)
            if result["ok"]:
                success_count += 1
            else:
                print("[approve-failed]", assignment_id, result.get("status_code"), result.get("message"), result.get("raw"))
                failed.append({
                    "assignment_id": assignment_id,
                    "message": result["message"],
                    "raw": result.get("raw", {})
                })

            # Check flag after each approval to stop faster
            if get_stop_flag(period_id):
                yield f'data: {json.dumps({
                    "done": True,
                    "stopped": True,
                    "total": total,
                    "success": success_count,
                    "failed_count": len(failed),
                    "first_error": failed[0] if failed else None
                })}\n\n'
                set_stop_flag(period_id, False)
                return

            yield f'data: {json.dumps({"progress": i, "total": total, "success": success_count, "failed": len(failed)})}\n\n'
            time.sleep(0.05)

        # yield f'data: {json.dumps({"done": True, "total": total, "success": success_count, "failed_count": len(failed), "failed_items": failed[:10]})}\n\n'
        set_stop_flag(period_id, False)  
        yield f'data: {json.dumps({
            "done": True,
            "total": total,
            "success": success_count,
            "failed_count": len(failed),
            "first_error": failed[0] if failed else None
        })}\n\n'

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )

def approve_assignment(req_session, assignment_id):
    url, meth, _ = get_api("APPROVE_ASSIGNMENT")
    try:
        res = req_session.request(
            meth,
            url,
            files={
                "assignmentId": (None, assignment_id),
                "statusApproval": (None, "true"),
                "comment": (None, '{"dataKey":"","notes":[]}')
            },
            timeout=10
        )
        raw = res.json()
        return {
            "ok": bool(raw.get("success")),
            "message": raw.get("message", ""),
            "data": raw.get("data", {}),
            "raw": raw,
            "status_code": res.status_code,
        }
    except Exception as e:
        return {
            "ok": False,
            "message": str(e),
            "data": {},
            "raw": {},
            "status_code": None,
        }

@app.route('/api/approve-stop', methods=['POST'])
def api_approve_stop():
    if not check_session():
        return jsonify({"error": "Sesi tidak aktif"}), 401

    body = request.get_json() or {}
    period_id = body.get("period_id", "")

    if not period_id:
        return jsonify({"error": "period_id diperlukan"}), 400

    set_stop_flag(period_id, True)
    return jsonify({"message": "Permintaan stop dikirim. Proses akan berhenti setelah item aktif selesai."})

# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    from werkzeug.middleware.dispatcher import DispatcherMiddleware
    from werkzeug.serving import run_simple

    # Clear session files on startup
    clear_session_cache()

    def dummy_app(environ, start_response):
        start_response('200 OK', [('Content-Type', 'text/plain')])
        return [b'']

    application = DispatcherMiddleware(dummy_app, {'/fasihsm-fetcher': app})
    run_simple('0.0.0.0', 5000, application, use_reloader=True, use_debugger=True, threaded=True)