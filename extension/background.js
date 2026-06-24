chrome.action.onClicked.addListener((tab) => {
  if (tab.url && tab.url.includes("bps.go.id")) {
    chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => navigator.userAgent
    }, (results) => {
      let ua = navigator.userAgent;
      if (results && results[0]) {
        ua = results[0].result;
      }

      const targetUrl = "https://fasih-sm.bps.go.id/survey/api/v1/surveys/datatable";
      const partitionKeys = [
        null,
        {},
        { topLevelSite: "https://bps.go.id" },
        { topLevelSite: "https://fasih-sm.bps.go.id" },
        { topLevelSite: "https://sso.bps.go.id" }
      ];

      const queries = [];
      partitionKeys.forEach(pk => {
        const q = { url: targetUrl };
        if (pk !== null) {
          q.partitionKey = pk;
        }
        queries.push(q);
      });

      const allCookies = [];
      const seen = new Set();
      let completed = 0;

      const checkFinish = () => {
        completed++;
        if (completed === queries.length) {
          if (allCookies.length === 0) {
            chrome.action.setBadgeText({ text: "FAIL" });
            chrome.action.setBadgeBackgroundColor({ color: "#dc3545" });
            return;
          }

          const cookieStr = allCookies.map(c => `${c.name}=${c.value}`).join("; ");
          const LOCAL_APP_URL = "http://127.0.0.1:5000/fasihsm-fetcher/import-session-cookies";

          fetch(LOCAL_APP_URL, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "Accept": "application/json"
            },
            body: JSON.stringify({
              session_text: "Cookie: " + cookieStr + "\nUser-Agent: " + ua
            })
          })
          .then(res => res.json())
          .then(data => {
            chrome.action.setBadgeText({ text: "OK" });
            chrome.action.setBadgeBackgroundColor({ color: "#28a745" });
            setTimeout(() => chrome.action.setBadgeText({ text: "" }), 3000);
          })
          .catch(err => {
            chrome.action.setBadgeText({ text: "ERR" });
            chrome.action.setBadgeBackgroundColor({ color: "#dc3545" });
            setTimeout(() => chrome.action.setBadgeText({ text: "" }), 3000);
          });
        }
      };

      queries.forEach(q => {
        try {
          chrome.cookies.getAll(q, (cookies) => {
            if (chrome.runtime.lastError) {
              console.error("Cookie query error:", chrome.runtime.lastError.message, q);
            }
            if (cookies) {
              for (const c of cookies) {
                if (!seen.has(c.name)) {
                  seen.add(c.name);
                  allCookies.push(c);
                }
              }
            }
            checkFinish();
          });
        } catch (e) {
          console.error("Cookie sync catch error:", e, q);
          checkFinish();
        }
      });
    });
  } else {
    chrome.action.setBadgeText({ text: "OPEN" });
    chrome.action.setBadgeBackgroundColor({ color: "#ffc107" });
    setTimeout(() => chrome.action.setBadgeText({ text: "" }), 3000);
  }
});
