# IDAL CGI protocol of the Orca touch display

Research output of subagent C (protocol analyst), Phase 1, 2026-10-31.
Static analysis only: nothing from the jar or the JavaScript was executed and no
device was contacted. Live facts quoted here come from the lead's captures
(`research/captures/`, gitignored).

Confidence tags: **H** = read directly from bytecode, HTML/JS or a live capture;
**M** = inferred from code plus corroboration; **L** = hypothesis to test live.

Placeholders: `<TOKEN>` = 32-hex session token, `<NOW>` = Unix time in seconds,
`<MS>` = Unix time in milliseconds, `<MAC>`, `<SERIAL>`, `<IP-…>` = values never
written down here. The pump's address `192.168.178.62` is known and allowed.

---

## 0. Key findings

1. **`LIMITS`, `SUBSTATUS` and `TIME_STAMP` are not request options.** `LIMITS`,
   `SUBSTATUS` and `QUALITY` are bit fields the applet decodes from the quality
   integer in each value line (`qqssssll`, OPC DA layout). `192` = good,
   non-specific, not limited. **readTags gives no min/max.** (H: `ICUdata.readQuality/readSubStatus/readLimits`,
   `ICUGateway.getCacheTagsByType`, `accessory.js:120-160`)
2. **`getProperties` is not tag metadata.** It reads IDAL system properties
   defined in the project's `propertymap.xml`. (H: `getsetproperties.html:516`,
   `library.js:1616-1670`)
3. **Tag metadata (type, access mode, scaling, EU min/max) is most likely
   available via `browse` with `returnObject=true`.** The console offers the
   `where` attributes `tagType`, `tagAccessMode`, `tagEnableLimits`, `tagEUMin`,
   `tagEUMax`, `tagS1..S3` and more. (H for the attribute names: `browse.html:384-416`;
   L for what `returnObject=true` returns)
4. **Alarm texts:** `browse` with `where=alarmName` lists alarm objects. The
   attributes include `alarmDescription` and `alarmSource`. `readAlarms` returns
   only event, state, source value and timestamp per alarm, no text. Project files
   named by the console: `alarms.xml`, `groups.xml`, `trends.xml`,
   `eventconfig.xml`, `propertymap.xml`. The old FTP dump also shows that
   `workspace/Project/Page109.jmx` is the page that displays `2_Vrsta_alarma`.
5. **`leasemng.html` has nothing to do with login sessions.** It drives
   `activateGroups` (group name plus a lease time in ms, returning an activation
   ID) and `deactivate`. Both endpoints are FORBIDDEN. (H: `leasemng.html:344,512`,
   `ICUGateway.activateGroups/deactivateGroup`)
6. **The jar predates `cgi/login`.** It authenticates with HTTP Basic
   (`exor.utils.AuthImpl` via `java.net.Authenticator`) and contains no `login`,
   `logout`, `E_NEED_LOGIN`, `E_TOO_MANY_USERS`, `E_PASS_DONT_MATCH` or
   `E_RE-LOGIN_ATTEMPT`. Session semantics therefore come from `root.html`,
   `INDEX.HTML`, the lead's captures and one third-party client of the same server
   family (Waterkotte EcoTouch, §1.3). (H)
7. **The HTTP 408 is almost certainly the ABYSS header buffer.** The server
   identifies as "IDAL - HTTP daemon, based on ABYSS Web Server 0.4". ABYSS reads
   the request header into a fixed `char buffer[4096]` and answers 408 when the
   header cannot be read. The prediction is that **the request line plus all
   header lines must fit in about 4,095 bytes**. With the probe's headers that
   puts the maximum request line at **3,990 characters**, which matches the
   observed 3,946 OK / 4,374 failed. (M; 2 requests in §7 confirm or refute it)
8. **The vendor client sends parameters as a POST body**, not a query string, for
   every parameterised endpoint, including readTags (`n=N&t1=…`). GET with a query
   is proven live for login/readTags/logout. Whether POST lifts the 4 KB limit is
   unknown and is tested in §7. (H for the jar; L for the limit)
9. **The vendor client parses readTags positionally**: it expects exactly one
   record per requested tag, in request order, and never re-requests. Random record
   loss is not part of the design. The earlier "dropped records" are better
   explained by whole-request failures such as the 408. (H for the parsing; M for the
   conclusion)
10. **`getTCPIPSettings` returns IP, netmask, broadcast, gateway and one more
    address (`SA`), and no MAC.** No allowlisted endpoint in the jar exposes a MAC,
    serial number or hostname. (H for the 2007 format; M for current firmware)
11. A related device family with the same IDAL server is reported to allow **2
    sessions** with an idle timeout of **about 5 minutes**, and to "not always
    respond with data" after state changes. That client re-logs-in on HTTP 500 and on
    `E_NEED_LOGIN`. (L for Orca: third-party claim about another product)

---

## 1. Sources

### 1.1 Static console files (saved by the lead without login, 2026-10-31)

| File | Role | Used for |
|---|---|---|
| `captures/console/root.html` | Login page, titled "1Tool Touch Editor Console Login" (Carel's rebrand of EXOR's tooling) | login URL, `rnd`, accepted responses |
| `console-carel/INDEX.HTML` | Console menu, `logout()` | logout semantics |
| `console-carel/ICUGateway.jar` | Signed EXOR applet `exor.icu.client.ICUGateway`, built 2007-03-09, class version 46 (Java 1.2) | every endpoint, parameter and parser |
| `scripts/liveConnect/library.js` (Carel, 2005) | JS↔applet bridge | how the console calls the applet, units, defaults |
| `scripts/liveConnect/accessory.js` | Helpers | quality bit layout, tab-separated tokens |
| `tags_rw.html`, `groups_r.html`, `leasemng.html`, `alarms.html`, `trend_r.html`, `browse.html`, `browsepropertygroup.html`, `manag.html`, `file_rw.html`, `getsetproperties.html`, `propertiesgroup.html`, `statusparameters.html`, `readeventarchive.html` | One console page per endpoint group | field names, option lists, notes naming project files |

Jar contents (unpacked to `.scratch/C/jar/`):

| Class | Size | Role |
|---|---|---|
| `exor/icu/client/ICUGateway` | 110 KB | The applet: one method per CGI endpoint, plus caches |
| `ICUdata` | 9.8 KB | Parser for one tag, trend sample or event record |
| `ICUalarm`, `ICUbrowse`, `ICUgroup`, `ICUtrend`, `ICUevent` | 3 KB each | Parsers per endpoint |
| `ICUcgi` | 1.4 KB | Interface of constants: status codes, alarm states, delimiters |
| `ICUtagsCache`, `ICUGateway$1/$2` | small | Cache; privileged file writer for readFile/writeFile |
| `exor/utils/AuthImpl` | 1.7 KB | Swing dialog "Enter Network Password" (HTTP Basic auth) |
| `exor/utils/Base64` (+ streams) | 12 KB | Base64 for readFile/writeFile `BINARY` mode |

**Method.** `javap` and `java` are not installed. I wrote a pure-data class-file
parser (`.scratch/C/tools/jdis.py`: constant pool, fields, methods, a bytecode
disassembler run with `python3 -I`) and disassembled every class to
`.scratch/C/out/*.txt`. Citations below give `Class.method@offset` (bytecode
offset) or `file:line`.

### 1.2 Live data (lead's captures)

- `captures/requests.jsonl`: 54 requests (console save, 1 login, 30 readTags,
  logout).
- `captures/2026-10-31_full_dump/pass*_batch*.txt`: raw readTags responses.
  One 150-tag batch got HTTP 408 in 12 ms in both passes (body: ABYSS 0.4 error
  page).
- `research/findings.md`: login/logout bodies, 708 `S_OK` and 1,059
  `E_UNKNOWNTAG` tags, quality always `192`.
- `../orca-energy-ha/development_resources/readme.md` (read-only): a Wireshark
  capture of Moja Orca traffic. It shows `Server: 0.4`, `Connection: close`,
  `Content-type: text/plain`, `client=OrcaTouch1172`, `_=<ms>`, URL-encoded
  `MK1_IME%282%29` answered as `#MK1_IME(2)`, and FTP access to
  `workspace/Project/config/` XML files.
- `../orca-energy-ha/development_resources/menu_to_field.yaml` (read-only): an
  older parse of an FTP dump of the same project family. It shows the layout
  `workspace/Project/<Page>.jmx` (`.jmx` is EXOR JMobile's page format), and that
  `Page109.jmx` displays `2_Vrsta_alarma`.

### 1.3 Online documentation

Searches for public EXOR IDAL / ICU CGI documentation found nothing (queries for
`IDALToken`, `cgi/readTags`, `E_TOO_MANY_USERS`, `E_RE-LOGIN_ATTEMPT`, "IDAL -
HTTP daemon", pGD Touch + CGI, JMobile + readTags). What I did find:

| URL | What it established | Confidence for Orca |
|---|---|---|
| https://raw.githubusercontent.com/OpenSIPS/opensips/00a7a89abf501959499091e7c67ae81971e2aa60/modules_obsolete/mi_xmlrpc/abyss_conn.h | ABYSS connection buffer: `#define BUFFER_SIZE 4096`, `char buffer[BUFFER_SIZE]` | M (later ABYSS lineage, same author base) |
| https://raw.githubusercontent.com/OpenSIPS/opensips/00a7a89abf501959499091e7c67ae81971e2aa60/modules_obsolete/mi_xmlrpc/abyss_http.c | ABYSS answers 408 when reading the request line or header fails | M |
| https://raw.githubusercontent.com/OpenSIPS/opensips/00a7a89abf501959499091e7c67ae81971e2aa60/modules_obsolete/mi_xmlrpc/abyss_conn.c | Each read is capped at `bufferSpace-1`; the buffer is not grown | M |
| https://raw.githubusercontent.com/marq24/ha-waterkotte/main/custom_components/waterkotte_heatpump/pywaterkotte_ha/__init__.py | Another IDAL-CGI device (Waterkotte EcoTouch). Login is `GET /cgi/login?username&password`, and the cookie comes from the response (`response.cookies`). Handled codes: `E_TOO_MANY_USERS`, `E_PASS_DONT_MATCH`, `E_NEED_LOGIN` (re-login and retry), HTTP 500 on readTags (re-login and retry), `E_INACTIVETAG`. `GET /cgi/readTags?n=&t1..&_=<ms>` without `client`, at most 75 tags per request. writeTags uses `returnValue=true&rnd=` (FORBIDDEN here). Logout is `GET /cgi/logout`. | M (same server family) |
| https://raw.githubusercontent.com/marq24/ha-waterkotte/main/README.md | The device "only allows 2 sessions"; sessions time out after about 5 min; it "will not always respond with data", usually after a status change; 75 tags per call is fine | L (different product) |
| https://flows.nodered.org/node/node-red-contrib-waterkotte | Calls the interface "EcoTouch / IDAL CGI". The `IDALToken` cookie is reused across reads. On 401/403/`#E` responses the client re-logs-in once. | L |
| https://www.exorint.com/faq/2017/06/14/where-projects-are-stored-into-pc-runtime-and-windows-client | The JMobile runtime keeps projects under `…\server\workspace` | M (supports `workspace/Project/…`) |

I extracted facts only and copied no vendor text.

### 1.4 Overall confidence

- Endpoint names, parameter names, the HTTP method used by the vendor client and
  the response grammar the vendor client expects: **H** for the 2007 server.
  The pump runs a newer server (it has `cgi/login`), so treat these as **M** for
  current firmware until the live script confirms each one.
- Anything about sessions, slot counts and timeouts: **L/M**. That is what §7
  measures.

---

## 2. Transport and common grammar

### 2.1 HTTP layer

- Server: ABYSS 0.4 derivative (`Server: 0.4`; 408 page footer). Every response
  carries `Connection: close`, so there is **one TCP connection per request** and
  no keep-alive or pipelining. `Content-type: text/plain`. (H: dump batch 04, old readme)
- Base URL: `http://<host>/cgi/<endpoint>`. The applet builds
  `http://<codebase-host>:<port>/` + `cgi/<name>`. (H: `ICUGateway.<init>`/`resetparam@50-88`)
- **Method used by the vendor client** (H, from `getOutputStream()` calls):
  - POST with an `application/x-www-form-urlencoded` body (Java default) for every
    endpoint with parameters.
  - GET without a body for `getTime`, `getLocalTime`, `getTCPIPSettings`,
    `getPLCStatus`, `getDLSSettings` and the forbidden `enterConfigMode`,
    `enterOperatingMode`, `reset`, `restart`, `rgprs`.
- **GET with the same parameters in the query string works** for login,
  readTags and logout (H: live), and for readTags/writeTags in Moja Orca and in
  the Waterkotte client. Assume it works for the other read endpoints too (M), and
  fall back to POST if GET returns `#E_INVALIDARG` (§7).
- Encoding: the applet concatenates parameters **without URL-encoding** (H:
  `ICUGateway.readTags@59-175`), so the server receives raw names. The server does
  percent-decode: Moja Orca's `MK1_IME%282%29` comes back as `#MK1_IME(2)` (H: old
  readme). Raw `(`/`)` also work (H: the lead's dump read `MK1_IME(2)` = `S_OK`).
  Percent-encode spaces, `&`, `+`, `#`, `%`, `=` and non-ASCII characters. Their
  encoded length counts towards the limit in §5.
- Authentication on the current firmware: cookie `IDALToken=<TOKEN>`, see §3.2.

### 2.2 Response grammar

Text lines separated by `\n` (LF; the dumps contain no CR). Fields are separated by
`\t`. The applet constants are `VAR_PREFIX='#'` and `FIELD_DELIMITER='\t'`.
(H: `ICUcgi` fields)

```
response      := whole_error | records
whole_error   := "#" STATUS "\n"                  ; first line, no TAB: applies to every item
records       := record*
record        := "#" NAME "\t" STATUS "\n" [payload]
payload       := one or more lines, present only when STATUS is S_OK (endpoint-specific)
```

- readTags and readGroups payload: `QUALITY "\t" VALUE "\n"`.
- Session endpoints (login, logout) start with a count line: login is
  `1\n#S_OK\nIDALToken=<TOKEN>`, logout is `1\n#S_OK`. (H: live) The `1` looks
  like a record count. Do not depend on it; search for the `#STATUS` line instead.
- Error pages from the HTTP layer (404, 408) are HTML:
  `<HTML><HEAD><TITLE>Error 408</TITLE>…`. (H)
- `root.html:90` accepts HTTP **200 or 500** for login, so some CGI errors come
  back with status 500 and a `#E_…` body. Waterkotte's client also sees HTTP 500
  on readTags and re-logs-in. (M) **Always parse the body, whatever the HTTP
  status.**

### 2.3 Quality integer (`qqssssll`)

Decoded by `ICUdata.readQuality = (q>>6)&3`, `readSubStatus = (q>>2)&15` and
`readLimits = q&3` (H: bytecode), and by `accessory.js:120-160` (H). The meanings
follow OPC DA (M):

| Field | Values |
|---|---|
| quality `qq` | 0 BAD, 1 UNCERTAIN, 2 n/a, 3 GOOD (`accessory.js:100-117`) |
| substatus `ssss` | OPC DA, e.g. BAD: 1 config error, 2 not connected, 3 device failure, 4 sensor failure, 5 last known value, 6 comm failure, 7 out of service. UNCERTAIN: 1 last usable value, 4 sensor not accurate, 5 EU units exceeded |
| limits `ll` | 0 not limited, 1 low limited, 2 high limited, 3 constant |

If `qq == 0`, the applet replaces the value with the string `BAD_QUALITY` (H:
`ICUdata.readValue`). Every value seen so far is `192` (GOOD, 0, 0).

### 2.4 Status codes

| Code | Where | Meaning / handling | Source |
|---|---|---|---|
| `S_OK` | all | success | H |
| `S_MOREDATA` | readTrend, readEvent | more samples; re-request from the last timestamp | H `fetchTrendValues@1034-1150` |
| `S_NODATA` | readEvent (and trends) | no samples in the window | H `ICUcgi`, `fetchEventValues@768` |
| `E_FAIL` | all | generic failure, whole request (`#E_FAIL`) or per item | H |
| `E_INVALIDARG` | all | malformed or missing parameter, whole request or per item | H |
| `E_UNKNOWNTAG` | readTags | tag not in the project; record has **no value line** | H (live, `ICUcgi`) |
| `E_READFORBIDDEN` / `E_WRITEFORBIDDEN` | tags | access mode denies it | H `ICUcgi` |
| `E_UNACTIVETAG` | tags | tag inactive; Waterkotte's firmware spells it `E_INACTIVETAG` | H `ICUcgi`; M |
| `E_TAG_NOT_BOUNDED_TO_A_TAG`, `E_BOUNDED_TAG_NOT_CONNECTED_TO_PROTOCOL` | tags | project configuration error | H `ICUcgi` |
| `BORDERS_EXCEEDED_WHEN_WRITING` | writeTags (forbidden) | value outside the tag limits | H `ICUcgi` |
| `E_NO_OBJECTS_FOUND` | browse | nothing matched | H `browse@454` |
| `E_UNKNOWNALARM` | readAlarms | unknown alarm name | H `ICUcgi` |
| `E_ALARM_ACKNOWLEDGE_REQUIRED`, `E_NEEDNOT_ACKNOWLEDGE_ALARM` | reset/ack (forbidden) | | H `ICUcgi` |
| `E_UNKNOWNTREND` | readTrend | | H |
| `E_UNKNOWNARCHIVE`, `E_NONEXISTING_TYPE`, `E_NONEXISTING_SUBTYPE`, `E_NOT_SUPPORTED` | readEvent | | H `fetchEventValues@577-620` |
| `E_UNKNOWNSOURCE` | alarms/trends | | H `ICUcgi` |
| `E_NEED_LOGIN` | any CGI | no or expired token | M (PLAN §5.1, Waterkotte client) |
| `E_TOO_MANY_USERS` | login | all session slots taken | M (PLAN §5.1, Waterkotte) |
| `E_PASS_DONT_MATCH` | login | wrong credentials | M (PLAN §5.1, Waterkotte) |
| `E_RE-LOGIN_ATTEMPT` | login | treated as success by the console, see §4 | H `root.html:92`; meaning L |

Alarm states (`ICUcgi`, H): `NOT_TRIGGERED`, `DISABLED`, `TRIGGERED`,
`TRIGGERED_NOT_ACKED`, `TRIGGERED_ACKED`, `NOT_TRIGGERED_ACKED`,
`NOT_TRIGGERED_NOT_ACKED`.

---

## 3. Endpoint reference

### 3.1 All endpoints found (44 names: 42 `cgi/…` strings in the jar, plus login and logout from the HTML)

Status against PLAN.md §2.2: **ALLOWED** (read-only, no need to ask), **R14**
(readFile, R14 rules only), **PHASE-6** (writeTags, user present), **FORBIDDEN**
(never call, in any form). `login`/`logout` come from `root.html`/`INDEX.HTML`; the
rest come from the jar.

| # | Endpoint | Status | Vendor method | Parameters (vendor client) | Jar method |
|---|---|---|---|---|---|
| 1 | `cgi/login` | ALLOWED | GET | `username`, `password`, `rnd` | (root.html:87) |
| 2 | `cgi/logout` | ALLOWED | GET | — (cookie) | (INDEX.HTML:23-41) |
| 3 | `cgi/readTags` | ALLOWED | POST | `n`, `t1..tn` (legacy `read()`: `it1..itn`) | `readTags`, `read`, `auxAsyncRead` |
| 4 | `cgi/browse` | ALLOWED | POST | `maxWait`, `maxResult`, `where`, `hasValue`, `contPt`, `returnObject` | `browse` |
| 5 | `cgi/getProperties` | ALLOWED | POST | `n`, `it1..itn` | `getProperties` |
| 6 | `cgi/readAlarms` | ALLOWED | POST | `n`, `al1..aln` | `readAlarms` |
| 7 | `cgi/readGroups` | ALLOWED | POST | `n`, `gr1..grn` | `readGroups` |
| 8 | `cgi/readIDALStatusParameters` | ALLOWED | POST | `n`, `parameterName1..n` | `readIDALStatusParameters` |
| 9 | `cgi/getTCPIPSettings` | ALLOWED | GET | — | `getTCPIPSettings` |
| 10 | `cgi/getPLCStatus` | ALLOWED | GET | — | `getPLCStatus` |
| 11 | `cgi/getTime` | ALLOWED | GET | — | `getTime` |
| 12 | `cgi/getLocalTime` | ALLOWED | GET | — | `getLocalTime` |
| 13 | `cgi/getDLSSettings` | ALLOWED | GET | — | `getDLSSettings` |
| 14 | `cgi/readTrend` | ALLOWED | POST | `tr`, `returnTS`, `returnRT`, `iso8601TS`, `startTime`, `endTime`, `deltaTime`, `nSamples`, `bounds` | `fetchTrendValues` |
| 15 | `cgi/readEvent` | ALLOWED | POST | `eventType`, `subType`, `returnTS`, `startTime`, `endTime`, `nEvents`, `deltaTime`, `bounds` | `fetchEventValues` |
| 16 | `cgi/getPropertyGroup` | ALLOWED | POST | `name`, `gIdName`, `gIdVal`, `n`, `it1..itn` | `getPropertyGroup` |
| 17 | `cgi/browsePropertyGroup` | ALLOWED | POST | `name`, `propName` | `browsePropertyGroup` |
| 18 | `cgi/readFile` | **R14** | POST | `MODE` (`ASCII`/`BINARY`), `PATH` | `readFile` |
| 19 | `cgi/writeTags` | **PHASE-6** | POST | `n`, `t1..tn`, `v1..vn` | `writeTags`, `write` |
| 20 | `cgi/writeFile` | FORBIDDEN | POST | `MODE`, `PATH`, `SIZE`, `FILE` | `writeFile` |
| 21 | `cgi/setTime` | FORBIDDEN | POST | `time` | `setTime` |
| 22 | `cgi/setLocalTime` | FORBIDDEN | POST | `sec`, `min`, `hour`, `day`, `month`, `year` | `setLocalTime` |
| 23 | `cgi/setDLSSettings` | FORBIDDEN | POST | `stdoff`…`dlsmm` (12) | `setDLSSettings` |
| 24 | `cgi/setTCPIPSettings` | FORBIDDEN | POST | `ip`, `nm`, `ba`, `gtwa`, `sa` | `setTCPIPSettings` |
| 25 | `cgi/setPLCStatus` | FORBIDDEN | POST | `stat` (RUN/STOP/RELOAD_FROM_FILE/RESET_WARM/RESET_COLD/RESET_HARD) | `setPLCStatus` |
| 26 | `cgi/enterConfigMode` | FORBIDDEN | GET | — | `enterConfigMode` |
| 27 | `cgi/enterOperatingMode` | FORBIDDEN | GET | — | `enterOperatingMode` |
| 28 | `cgi/reset` | FORBIDDEN | GET | — | `reset` |
| 29 | `cgi/restart` | FORBIDDEN | GET | — | `restart` |
| 30 | `cgi/setProperties` | FORBIDDEN | POST | `n`, `it`, `v` | `setProperties` |
| 31 | `cgi/setPropertyGroup` | FORBIDDEN | POST | `name`, `gIdName`, `gIdVal`, `n`, `it`, `v` | `setPropertyGroup` |
| 32 | `cgi/addPropertyGroup` | FORBIDDEN | POST | same as 31 | `addPropertyGroup` |
| 33 | `cgi/deletePropertyGroup` | FORBIDDEN | POST | `name`, `gIdName`, `gIdVal`, `n` | `deletePropertyGroup` |
| 34 | `cgi/activateGroups` | FORBIDDEN | POST | `n`, `gr<i>`, `leaseTime<i>` | `activateGroups` |
| 35 | `cgi/deactivate` | FORBIDDEN | POST | `n`, `ai<i>` (activation ID) | `deactivateGroup` |
| 36 | `cgi/resetAlarms` | FORBIDDEN | POST | `n`, `al<i>` | `resetAlarms` |
| 37 | `cgi/acknowledgeAlarms` | FORBIDDEN | POST | `n`, `al<i>` | `acknowledgeAlarms` |
| 38 | `cgi/deleteTrendFile` | FORBIDDEN | POST | `tr` | `deleteTrendFile` |
| 39 | `cgi/dumpTrendFile` / `cgi/dumpAllTrendFiles` | FORBIDDEN | POST | `tr`, `folder` / `folder` | `dumpTrendFile`, `dumpAllTrendFiles` |
| 40 | `cgi/deleteEventArchive` / `cgi/dumpArchiveFile` / `cgi/dumpAllArchiveFiles` | FORBIDDEN | POST | `archive`, `folder` | `deleteEventArchive`, `dumpArchiveFile`, `dumpAllArchiveFilesHandler` |
| 41 | `cgi/rgprs` | FORBIDDEN | GET | — (recycle the GPRS connection) | `recycleGRPS` |

Count: 17 ALLOWED, 1 R14, 1 PHASE-6, 25 FORBIDDEN. Rows 39 and 40 combine 5
endpoints, so there are 44 endpoint names in total. The forbidden rows exist only
so that client code and reviews can recognise them. The live script uses none of
them.

### 3.2 `cgi/login` (ALLOWED)

- Request: `GET /cgi/login?username=<u>&password=<p>&rnd=<MS>` (H: `root.html:87`).
  The console `escape()`s username and password. `rnd` is
  `new Date().getTime()`, a cache-buster; the server most likely ignores it (M).
  The lead's probe logged in without `rnd` (H).
- Success: HTTP 200, body `1\n#S_OK\nIDALToken=<32 hex>` (H: live, 50 bytes, 12 ms).
- The token is a cookie. The console never sets `document.cookie`, yet its
  following page loads work, so the server most likely also sends
  `Set-Cookie: IDALToken=…`. Waterkotte's client relies on `response.cookies` (M).
  **Record the response headers live** (§7, S1-01).
- Failure bodies: `#E_TOO_MANY_USERS`, `#E_PASS_DONT_MATCH`, possibly with HTTP
  500 (`root.html:90` accepts 500) (M).
- `#E_RE-LOGIN_ATTEMPT`: the console treats it like `#S_OK` and goes on to the
  console pages (H: `root.html:92`). Most likely meaning (L): the request already
  carries a valid `IDALToken` cookie (a browser re-login), the server keeps the
  existing session, and it issues no new token. §7 tests this.

### 3.3 `cgi/logout` (ALLOWED)

- Request: `GET /cgi/logout` with `Cookie: IDALToken=<TOKEN>`; no parameters
  (H: `INDEX.HTML:23-41`, every console page's `logout()`).
- Success: `1\n#S_OK`; the console checks `#s_ok` case-insensitively (H: live,
  INDEX.HTML).
- Not known yet: the response for a stale or absent token, and whether the slot is
  freed at once. Tested in §7 (S1-90…93, S4).

### 3.4 `cgi/readTags` (ALLOWED)

**Request.**
- Vendor client: `POST /cgi/readTags`, body `n=<N>&t1=<tag1>&…&t<N>=<tagN>` (H:
  `ICUGateway.readTags@59-175`).
- Proven live: `GET /cgi/readTags?client=<any>&n=<N>&t1=…` (H).
- The legacy `read()` used `it<i>=` instead of `t<i>=` (H: `read@104`). Do not
  use it.
- `client`: in neither the jar nor the Waterkotte client. Moja Orca sends
  `client=OrcaTouch1172`, the probe sends `client=orca_probe`. Most likely it is
  ignored, or used as an identifier for logging or caching (L). S1-03 compares the
  responses.
- `_=<MS>` (Moja Orca/jQuery) is a cache-buster. It is harmless and unneeded.
- `n` must equal the number of `t<i>` parameters, which are numbered from 1. The jar
  has no upper limit on `n`. The real limit is the request size (§5).
- **There are no option parameters.** `LIMITS`, `SUBSTATUS`, `QUALITY`, `VALUE` and
  `ERROR_CODES` are client-side views on the parsed record (`getCacheTagsByType`
  type strings) (H). `TIME_STAMP` exists only for trend and event samples (H:
  `getCacheTrends`, `getCacheEvents`).

**Response** (H: dump, `readTags@308-770`):
```
#<tag>\tS_OK\n<quality>\t<value>\n          ; one record per requested tag
#<tag>\t<E_CODE>\n                          ; non-S_OK: NO value line
```
- Whole-request errors: a first line of `#E_INVALIDARG` or `#E_FAIL` with no tab.
  The applet then marks every tag with that code (H: `readTags@315-586`). Expect
  `#E_NEED_LOGIN` in the same position (M).
- The applet reads records **positionally**: record *i* belongs to tag *i*, and
  the parser reads a value line only for `S_OK` (and nothing for `E_FAIL` or other
  codes) (H). The server therefore answers in request order with exactly N records.
  This matches the dumps.
- Value: everything after the first tab on the value line. `ICUdata` tokenises on
  whitespace (H), but the older `read()` takes `substring(indexOf('\t')+1)` (H).
  Use the latter so that string values with spaces survive.
- Example (H, `pass1_batch01.txt`): `#2_Temp_vode_sanitarna\tS_OK\n192\t420\n`.

### 3.5 `cgi/browse` (ALLOWED): tag, alarm, trend and group enumeration

**Request.**
- Vendor client: POST body
  `maxWait=<ms>&maxResult=<n>&where=<attr>&hasValue=<pattern>&contPt=<cp>&returnObject=<true|false>`
  (H: `ICUGateway.browse@134-301`). `contPt` is sent empty when the caller passes
  `0`.
- The jar refuses locally when `where` or `hasValue` is empty, `maxWait<1`,
  `maxResult<1` or `contPt=="-1"` (H: `browse@15-63`).
- Console defaults: `maxWait=10000`, `maxResult=1000` (H: `library.js:1061-1062`).
  `maxWait` is the longest time the server may take; `maxResult` is the most
  results it may return (H: `browse.html:1182-1188`).
- `hasValue` is a pattern; the console's example is `demo*` (H: `browse.html:1184`).
  Whether it is a glob or a regex is open: try `*` first, then `.*`.
- `where` values offered by the console (H: `browse.html`):
  - tags (`:384-416`): `tagName`, `tagDevice`, `tagType`, `tagRefreshTime`,
    `tagResourceLocator`, `tagAccessMode`, `tagActive`, `tagEnableScaling`,
    `tagS1`, `tagS2`, `tagS3`, `tagEnableLimits`, `tagEUMax`, `tagEUMin`
  - groups (`:556-560`): `groupName`, `groupActive`, `groupHaveMember`
  - trends (`:704-720`): `trendName`, `trendSource`, `trendSamplingTime`,
    `trendCompressed`, `trendSize`, `trendActive`, `trendTrigger`,
    `trendLowLimit`, `trendHighLimit`
  - alarms (`:864-890`): `alarmName`, `alarmSource`, `alarmDescription`,
    `alarmEnabled`, `alarmRequireAck`, `alarmEnableLog`, `alarmLogMask`,
    `alarmNotifyMask`, `alarmActionMask`, `alarmEnableAction`, `alarmScript`,
    `alarmScriptFile`, `alarmSeverity`, `alarmPriority`
  - protocols (`:1038-1048`): `protocolName`, `protocolTimeout`,
    `protocolMaxLenght` (sic, the value sent), `protocolConfiguration`,
    `protocolFilename`, `protocolEnableOpt`
- `returnObject=false` returns object names. `returnObject=true` returns "objects"
  (H: `browse.html:29-37`). Their format is unknown (L): probably the object with
  its attributes, which would give type, access mode, scaling and EU min/max for
  tags, and the description for alarms.

**Response** (H: `browse@436-568`, `ICUbrowse.<init>`):
```
#S_OK\n
<token1>[\t<contPt>]\n      ; token1 unused by the applet (probably a count); contPt present = more results
<object name or object>\n   ; one per line
…
```
- Errors: `#E_FAIL`, `#E_NO_OBJECTS_FOUND` (single line). Anything else in the
  first line ends parsing.
- **Paging:** if line 2 carries a continuation point, repeat the same query with
  `contPt=<value>`, which appends the next page (H: `setCacheBrowse@126-227`,
  `library.js:1083-1092`).
- **Can it enumerate all tags?** Yes, by design: `where=tagName&hasValue=*`, paged
  with `maxResult` and `contPt` (M; L until S1-20…22).

### 3.6 `cgi/getProperties` (ALLOWED)

- Request: POST/GET `n=<N>&it1=<propertyName>&…` (H: `getProperties@54-171`).
- Names: IDAL properties listed in the project's `propertymap.xml` (H:
  `getsetproperties.html:516`). They are **not tags**. Do not send tag names
  expecting metadata.
- Response per item: `#<name>\t<STATUS>\n` and, if `S_OK`, one line holding the
  value (the whole line) (H: `getProperties@336-515`). A line without a tab is
  taken as a whole-request error.

### 3.7 `cgi/readAlarms` (ALLOWED)

- Request: POST/GET `n=<N>&al1=<alarmName>&…` (H: `readAlarms@64-173`). Names come
  from `alarms.xml` (`alarms.html:520`), i.e. from `browse where=alarmName`.
- Response per alarm (H: `readAlarms@600-748`, `ICUalarm.<init>`):
  ```
  #<alarmName>\tS_OK\n<event>\t<state>\t<sourceValue>\t<timestamp>\n
  #<alarmName>\t<E_CODE>\n                     ; e.g. E_UNKNOWNALARM, no second line
  ```
  - `state` is one of the alarm states in §2.4.
  - `event` and `timestamp` formats are unknown (timestamp: probably Unix seconds, L).
  - The parser splits on whitespace, so none of the four fields contains spaces.
  - **There is no alarm text.**
- Whole-request errors: `#E_INVALIDARG`, `#E_FAIL`.
- Never send `acknowledgeAlarms` or `resetAlarms`. They take the same parameters,
  which makes them easy to confuse.

### 3.8 `cgi/readEvent` (ALLOWED): event archive and alarm history

- Request: POST/GET
  `eventType=<type>&subType=<int>&returnTS=<true|false>&startTime=<s>&endTime=<s>&nEvents=<int>&deltaTime=<float>&bounds=<true|false>`
  (H: `fetchEventValues@179-433`).
- Times are Unix seconds; the console sends `Date.getTime()/1000` (H:
  `library.js:704-929`). Its fallback window is "5 min to 4.5 min ago".
- `nEvents=0` and `deltaTime=0` mean unset. The console note gives `deltaTime` in
  milliseconds (`readeventarchive.html:924-930`).
- `eventType` and `subType` come from the project's **`eventconfig.xml`** (H:
  `readeventarchive.html:924`). They are not discoverable through browse.
- Response (H: `fetchEventValues@570-1113`, `ICUevent`,
  `ICUdata.<init>(String,ZZI)`):
  ```
  #<eventType>\t<S_OK|S_MOREDATA|S_NODATA|E_INVALIDARG|E_FAIL|E_UNKNOWNARCHIVE>\n
  #<eventType>\t<subType>\t[<timestamp>\t]<text …>\n      ; one line per event
  ```
  - The first token loses its first character (the `#`).
  - `<timestamp>` (a Unix long) is present when `returnTS=true`.
  - **The rest of the line, with spaces, is the event value/text.** For alarm
    events this may be the alarm message (L).
  - Whole-request errors: `#E_INVALIDARG`, `#E_NONEXISTING_TYPE`,
    `#E_NONEXISTING_SUBTYPE`, `#E_NOT_SUPPORTED`.
  - `S_MOREDATA`: page by re-requesting from the last timestamp, like readTrend (M).

### 3.9 `cgi/readGroups` (ALLOWED)

- Request: POST/GET `n=<N>&gr1=<group>&…` (H: `readGroups@88-195`). Group names are
  in `groups.xml` (`groups_r.html:490`), i.e. `browse where=groupName`.
- Response (H: `setCacheGroups`, `ICUgroup`):
  ```
  #<group>\t<STATUS>\n
  #<tag>\tS_OK\n<quality>\t<value>\n     ; the group's member tags, as readTags
  … next #<group> header …
  ```
  Groups are split at header lines that match a requested group name. Whole-request
  errors: `#E_FAIL`, `#E_INVALIDARG`.
- Use: groups.xml presumably holds the HMI's own polling groups. A group that
  matches what we need could replace a long readTags request (L).

### 3.10 `cgi/readIDALStatusParameters` (ALLOWED)

- Request: POST/GET `n=<N>&parameterName1=<name>&…` (H:
  `readIDALStatusParameters@54-177`).
- Names: "see CGI interface documentation" (H: `statusparameters.html:399`). That
  document was not found, so the names are unknown.
- Response per item: same as getProperties (§3.6).

### 3.11 `cgi/getTCPIPSettings` (ALLOWED)

- Request: `GET /cgi/getTCPIPSettings` (H). The applet sets `doOutput` but never
  writes a body, so the request stays a GET.
- Response (H: `getTCPIPSettings@126-377`, `manag.html:1261-1287, 2487-2531`):
  `#S_OK\n<IP>\n<NM>\n<BA>\n<GW>\n<SA>`, that is IP address, netmask, broadcast
  address, gateway and `SA` (probably a server address such as DNS or SNTP; L).
  The applet reads exactly 5 lines after the status. **There is no MAC** in this
  format. Newer firmware might add lines, so record the full body. Error:
  `#E_FAIL`. These values are network details: keep them in captures only.

### 3.12 `cgi/getPLCStatus` (ALLOWED)

- Request: `GET /cgi/getPLCStatus`.
- Response: `#S_OK\n<status>` (H: `getPLCStatus@126-272`). The status is probably
  one of RUN / STOP / … (the `setPLCStatus` option list, `manag.html:2559-2573`)
  (L).
- On EXOR panels "PLC" is the panel's internal soft-PLC, not the Carel pCO
  controller (L). Low value; cheap.

### 3.13 `cgi/getTime`, `cgi/getLocalTime`, `cgi/getDLSSettings` (ALLOWED)

- `GET /cgi/getTime` → `#S_OK\n<time>`. `GET /cgi/getLocalTime` →
  `#S_OK\n<local time>`. (H: `getTime@133-279`, `getLocalTime@126-272`) The formats
  are unknown: getTime is probably Unix seconds (setTime takes `time=`), and
  getLocalTime is probably a formatted local time (`manag.html:1141` shows it raw)
  (L).
- `GET /cgi/getDLSSettings` → `#S_OK\n` followed by 13 lines (H:
  `getDLSSettings@218-307`, `library.js:2227-2347`):
  1. std offset (minutes as uint16, two's complement)
  2. std week (1–5, 5 = last)
  3. std day (0 = Sunday)
  4. std month (0 = January)
  5. std hour
  6. std minute
  7. dls offset
  8. dls week
  9. dls day
  10. dls month
  11. dls hour
  12. dls minute
  13. mode

  The applet returns `E_FAIL` otherwise.
- Use: the pump clock and timezone, which matter for readEvent/readTrend windows
  and for the `2_CURRENT_*` tags.

### 3.14 `cgi/readTrend` (ALLOWED)

- Request: POST/GET
  `tr=<trend>&returnTS=<bool>&returnRT=<bool>&iso8601TS=<bool>&startTime=<s>&endTime=<s>&deltaTime=<float>&nSamples=<int>&bounds=<bool>`
  (H: `fetchTrendValues@179-470`). Times are Unix seconds (H: `library.js:560-603`).
  Trend names are in `trends.xml` (`trend_r.html:1164`), i.e. `browse where=trendName`.
- Response:
  ```
  #<trend>\t<S_OK|S_MOREDATA|E_UNKNOWNTREND>\n
  [<timestamp>\t][<refreshTime>\t]<quality>\t<value>\n     ; one per sample
  ```
  The timestamp is present if `returnTS` (an ISO string if `iso8601TS`, otherwise a
  long). The refresh time is present if `returnRT`. Whole-request error: `#E_FAIL`.
- `S_MOREDATA`: the applet re-requests with `startTime = <last sample's timestamp>`
  (or `endTime`, when `startTime > endTime`) (H: `fetchTrendValues@1042-1155`).

### 3.15 `cgi/getPropertyGroup`, `cgi/browsePropertyGroup` (ALLOWED)

- `getPropertyGroup`: POST/GET
  `name=<group>&gIdName=<idName>&gIdVal=<idValue>&n=<N>&it1=<prop>&…`. The response
  per item is the same as getProperties (H: `getPropertyGroup@56-564`). Groups and
  properties come from `propertymap.xml` (`propertiesgroup.html:452`).
- `browsePropertyGroup`: POST/GET `name=<group>&propName=<prop>` (H:
  `browsePropertyGroup@64-110`). The response is `#S_OK\n` followed by one value per
  line until EOF: all instances of that property in the group (H: `@224-431`).
  Otherwise there is a single error line.

### 3.16 `cgi/readFile` (R14 only)

- Request: POST body `MODE=<ASCII|BINARY>&PATH=<server path>` (H: `readFile@59-184`).
  The parameter names are upper case. GET with the same query is untested (M).
- Paths: "Use absolute paths" (H: `file_rw.html:584`). Separator and root are
  unknown (§7, S2).
- Response (H: `readFile@222-653`):
  ```
  #S_OK\n
  <size>\n                       ; integer; the applet parses it with parseInt
  <content lines …>              ; ASCII: the file text. BINARY: Base64 lines (exor.utils.Base64)
  ```
  Otherwise the first line is a `#E_…` code.
- The client side does not URL-encode, so encode spaces as `%20` (some page files
  have spaces in their names).
- **Directory listing:** no CGI endpoint in the jar lists directories, and readFile
  documents none. Whether readFile on a directory path returns a listing is
  untested (L, one request in §7).
- **Project files that IDAL itself names** (H: console notes):
  - `alarms.xml`: alarm definitions; likely name, source tag and description/text
  - `groups.xml`
  - `trends.xml`
  - `eventconfig.xml`: event types and subtypes for readEvent
  - `propertymap.xml`: names for getProperties and property groups
- From the old FTP dump (H: old readme, menu map): these live in
  `workspace/Project/config/`, and the UI pages are `workspace/Project/<Page>.jmx`.
  `Page109.jmx` shows `2_Vrsta_alarma` and is the best candidate for the
  **alarm-code → text** map (M).
- JMobile `.jmx` pages bind widgets to tags and hold message lists (UI labels, enum
  texts) (M).
- Never read credential files (for example user or password stores).

### 3.17 `cgi/writeTags` (PHASE-6) and the FORBIDDEN endpoints

Documented in §3.1 only. writeTags: POST `n=<N>&t1=<tag>&v1=<value>…`; the response
uses readTags records. The Waterkotte client adds `returnValue=true&rnd=` (M). It is
not used before Phase 6.

---

## 4. Session and lease semantics (R1)

| Question | Static answer | Confidence | Live test |
|---|---|---|---|
| What is "lease management"? | Activation of tag groups (`activateGroups`: group plus lease time in ms, returning an activation ID and lease time; `deactivate` by activation ID). The server presumably keeps a group refreshed while its lease runs. **Unrelated to login sessions; both endpoints FORBIDDEN.** | H | none |
| How is a session created? | `GET /cgi/login` → `IDALToken` in the body, and probably in `Set-Cookie` as well | H / M | S1-01 records headers |
| Max sessions | Not in the static files. A related device: 2 | L | S4 (gated) |
| Idle timeout | Not in the static files. A related device: about 5 min | L | S3 |
| Do reads keep a session alive? | Unknown. The 2007 applet has no keep-alive, and the Waterkotte client simply re-logs-in on `E_NEED_LOGIN`. | L | S3 keep-alive phase |
| What does logout do? | Returns `1\n#S_OK`. Most likely destroys the token server-side, freeing the slot. | M | S1-91 (stale token → `E_NEED_LOGIN`?), S4 (slot freed at once?) |
| `E_RE-LOGIN_ATTEMPT` | Login while presenting a still-valid token; the console treats it as success and keeps using the existing session | L | S2-01 (stale cookie, safe), S4 (valid cookie, gated) |
| `E_NEED_LOGIN` | Token missing, unknown or expired → log in again | M | S1-92/93 |
| Leaked sessions | The old integration never logged out. Its slots free themselves after the idle timeout. The login on 2026-10-31 succeeded at once, so no leak was blocking. | H (observation) | — |
| Is `rnd` meaningful? | Cache-buster only | M | — |

---

## 5. Limits (R11)

1. **Request header size (the 408).**
   - Observations (H): request lines (counted as `GET <target> HTTP/1.1`) of 3,946
     characters worked and 4,374 got HTTP 408 in 12 ms, deterministically.
   - Explanation (M): ABYSS reads the request line and headers into a 4,096-byte
     connection buffer. A read is capped at 4,095 bytes. If the header block is not
     complete when the buffer is full, the read fails and ABYSS answers 408 at once.
     A real timeout would take seconds.
   - Prediction: request line + CRLF + every header line + the final CRLF ≤ 4,095
     bytes. The probe's headers are `Host: 192.168.178.62` (22 bytes with CRLF),
     `Accept-Encoding: identity` (27) and `Cookie: IDALToken=<32>` (52), plus the
     final CRLF (2): 103 bytes on top of the request line and its own CRLF. That
     gives a maximum request line of **3,990**.
   - aiohttp sends other headers (`User-Agent: Python/3.x aiohttp/x`, `Accept`,
     `Accept-Encoding: gzip, deflate`), so the client must budget by bytes **after**
     building the headers.
   - S1-25…27 verify the prediction with 3 requests.
2. **POST body.** Unknown. If the CGI handler reads the body through the same
   buffer, the limit is similar. If it reads it separately, POST would allow large
   batches. There is a small risk that an oversized body stalls the handler until
   its timeout. Tested last and optionally (S1-38).
3. **Tags per request.** No count limit in the jar. 150 tags worked when they fit
   the byte budget (H). Waterkotte uses at most 75 (L). The limit is effectively
   the byte budget. An optional count test is S1-39.
4. **Concurrency.** The server closes every connection. The vendor client issues
   one request at a time per action. ABYSS 0.x may be single-threaded (L). Do not
   send concurrent requests (PLAN §7.2 already requires one lock).
5. **Latency.** 12–94 ms per readTags of 150 tags (~5 KB) (H, requests.jsonl).
6. **Missing records.** None in 2 × 1,767 tags apart from the deterministic 408
   (H, findings). The applet's positional parser assumes no record loss (H). A
   related device "does not always respond" after state changes (L). S1-50…89
   measure this.

---

## 6. Device identity and discovery (R3, R5, R13)

| Item | Where it might be | Confidence |
|---|---|---|
| IP, netmask, broadcast, gateway, SA | `getTCPIPSettings` | H (format) |
| MAC | **Not** in any allowlisted endpoint's 2007 format. Options: the lead's own ARP cache after any request (`ip neigh show 192.168.178.62`, local and passive, OUI only in sanitised notes); HA DHCP discovery supplies `macaddress` | H / M |
| Hostname | Not exposed by the CGI. Only via DHCP (router or HA DHCP discovery) | M |
| Serial number, IDAL/runtime version | Possibly IDAL properties (`propertymap.xml` → getProperties) or status parameters (names unknown) | L |
| Controller firmware | Tags `2_Verzija_programa_LETO/MESEC/DAN/ZAPOREDJE` exist in `all_fields.txt` (agent A/R5) | M |
| Panel clock and timezone | `getTime`, `getLocalTime`, `getDLSSettings` | H (endpoint) |
| Protocol to the controller | `browse where=protocolName` (+ `returnObject=true`) | L |
| Server software | `Server: 0.4` header; ABYSS 0.4 footer on error pages | H |
| Stable unique ID for HA | Best candidate: the MAC from DHCP or ARP. Fallback: a property or serial if R14/S2 finds one. Last resort: the host plus the user's chosen name. | M |

---

## 7. Live-test script for the lead

### 7.0 Before running

1. **Review** every request below against PLAN §2.2. Only allowlisted endpoints
   appear: `login`, `logout`, `readTags`, `browse`, `readAlarms`, `readGroups`,
   `readTrend`, `readEvent`, `getTCPIPSettings`, `getPLCStatus`, `getTime`,
   `getLocalTime`, `getDLSSettings`, `getProperties`, `getPropertyGroup`,
   `browsePropertyGroup`, `readIDALStatusParameters`, and `readFile` in the R14
   block only. No writeTags; nothing from the never-call list.
2. Make sure no HA instance you control polls the pump. Ideally ask the user to
   close Moja Orca. Its cloud proxy logs into the pump and uses a slot.
3. Proposed probe extensions (`tools/orca_probe.py`), none of which widen the
   allowlist:
   - (a) `Display.post(path, body)` with
     `Content-Type: application/x-www-form-urlencoded` (vendor method).
   - (b) Log response **headers** (`Set-Cookie`, `Server`, `Content-Type`,
     `Connection`, `Content-Length`) and the exact request-line length plus the
     total header bytes sent.
   - (c) An optional extra request header (`X-Pad`) for S1-27 only.
   - (d) A separate `readfile` command that refuses any path not in an explicit
     per-run list, issues one request at a time, saves to
     `research/captures/readfile/`, and stops at the first unexpected response.
   - (e) Never request tags whose name contains `GESLO` (case-insensitive), and
     redact them if they appear in any capture.
   - (f) Redact `IP`/`MAC`/serial values in anything written outside `captures/`.
   - (g) Keep `REQUEST_PAUSE = 1 s` and `TIMEOUT = 30 s`.
4. Request target notation: `GET /cgi/x?…` means the probe's GET with the cookie
   once logged in.

### 7.1 Global stop conditions (all sessions)

- Login `#E_TOO_MANY_USERS` (except inside S4, where it is the measurement): back
  off 1, 2, 4 and 8 min, then stop and ask the user.
- Any timeout, connection refused/reset, or HTTP status not expected by the step:
  stop the session, log out (in `finally`), wait 5 min, then check health once with
  a no-login `GET /`. Report to the user if it is not 200.
- `#E_NEED_LOGIN` before Session 3: stop and log out. Re-login at most once per
  session, and only where a step says so.
- Any response that suggests a state change (it should be impossible with these
  endpoints): stop and report.
- Every session ends with `GET /cgi/logout` in `finally`, also after errors.

### 7.2 Session 1: discovery, R2/R3/R4/R11 (1 login, about 95–105 requests, ~5 min)

Ordered by value and safety. Save every raw body.

| Step | Purpose | Request | Expect | Record / notes |
|---|---|---|---|---|
| S1-01 | login, R1 | `GET /cgi/login?username=admin&password=admin&rnd=<MS>` | `1\n#S_OK\nIDALToken=<TOKEN>` | all response headers (Set-Cookie?) and timing |
| S1-02 | baseline | `GET /cgi/readTags?client=orca_probe&n=8&t1=2_Temp_vode_sanitarna&t2=2_Rezim_MK1&t3=2_Temp_Zunanja&t4=2_SV_vklop&t5=2_Temp_RF2&t6=2_NAPAKA&t7=MK1_IME(2)&t8=2_CURRENT_SECOND` | 7 × `S_OK` (`2_Temp_RF2` = -9999), `#2_NAPAKA\tE_UNKNOWNTAG` without a value line | record order; positional? |
| S1-03 | is `client` meaningful? | same as S1-02 without `client=orca_probe&` | identical records | diff the bodies |
| S1-04 | POST equivalence | `POST /cgi/readTags`, body `n=8&t1=…&t8=2_CURRENT_SECOND` | identical records | if it is not identical, skip S1-38 |
| S1-05 | R3/R13 | `GET /cgi/getTCPIPSettings` | `#S_OK` + 5 lines | the whole body; count the lines (more than 5? a MAC?). Captures only. |
| S1-06 | R5 | `GET /cgi/getPLCStatus` | `#S_OK\n<status>` | |
| S1-07 | clock | `GET /cgi/getTime` | `#S_OK\n<time>` | format; compare with `<NOW>` |
| S1-08 | clock | `GET /cgi/getLocalTime` | `#S_OK\n<time>` | format |
| S1-09 | clock | `GET /cgi/getDLSSettings` | `#S_OK` + 13 lines | |
| S1-10 | **R4 alarm list** | `GET /cgi/browse?maxWait=10000&maxResult=1000&where=alarmName&hasValue=*&contPt=&returnObject=false` | `#S_OK\n<x>[\t<cp>]\n<name>…` | names, count, contPt. On `#E_INVALIDARG`, repeat once as POST. On `#E_NO_OBJECTS_FOUND`, repeat once with `hasValue=.*`. |
| S1-11 | **R4 alarm texts** | same as S1-10 with `returnObject=true` | objects incl. description/source | the format (any attributes, any languages?) |
| S1-12 | R4 states | `GET /cgi/readAlarms?n=<k>&al1=<name1>…` for all names from S1-10, batched ≤ 3,500-char request lines (%20 for spaces) | `#<name>\tS_OK\n<event>\t<state>\t<src>\t<ts>` | states, timestamps; any `TRIGGERED*` → note the current alarm |
| S1-13 | R2/R12 tag metadata | `GET /cgi/browse?maxWait=10000&maxResult=10&where=tagName&hasValue=2_Temp_vode_sanitarna&contPt=&returnObject=true` | one object | attributes: type, access mode, EU min/max, scaling? |
| S1-14 | ditto, enum | same with `hasValue=2_Rezim_MK1` | | |
| S1-15 | ditto, read-only sensor | same with `hasValue=2_Temp_Zunanja` (`2_Temp_AF` is not a tag on this pump) | | does access mode differ from S1-13? |
| S1-16 | ditto, boolean | same with `hasValue=2_SV_vklop` | | |
| S1-17 | groups | `GET /cgi/browse?maxWait=10000&maxResult=1000&where=groupName&hasValue=*&contPt=&returnObject=false` | names or `#E_NO_OBJECTS_FOUND` | |
| S1-18 | trends | as S1-17 with `where=trendName` | | |
| S1-19 | protocols (optional) | as S1-17 with `where=protocolName&returnObject=true` | | controller protocol and address (R5) |
| S1-20 | paging | `GET /cgi/browse?maxWait=10000&maxResult=100&where=tagName&hasValue=*&contPt=&returnObject=false` | 100 names + contPt | does the contPt format make sense? |
| S1-21 | paging | same with `contPt=<cp from S1-20>` | the next 100 | no overlap with S1-20 |
| S1-22 | **R2 full tag list** | as S1-20 with `maxResult=1000`, following contPt, at most 5 pages; stop if a page takes > 10 s | all tag names | total; compare with the 708 `S_OK` set and `all_fields.txt`. Redact nothing (names only), but read no GESLO values. |
| S1-23 | groups content | `GET /cgi/readGroups?n=<≤3>&gr1=<g1>…` if S1-17 found groups | header plus records | which tags the HMI groups |
| S1-24 | trend sample | `GET /cgi/readTrend?tr=<t1>&returnTS=true&returnRT=false&iso8601TS=false&startTime=<NOW-86400>&endTime=<NOW>&deltaTime=0.0&nSamples=20&bounds=false` if S1-18 found trends | samples | sample format |
| S1-25 | **R11 limit model** | readTags of known `S_OK` tags (no GESLO), padded through the `client=` value (if S1-03 showed it is ignored) to a request line of exactly **3,990** chars | 200 + records | header bytes sent |
| S1-26 | R11 | the same at exactly **3,991** chars | instant 408 | if not 408 → binary search up to 4,374 (≤ 5 requests, 16-byte resolution) |
| S1-27 | R11 header vs. line | a 3,900-char request line plus header `X-Pad: <100 × a>` | 408 (header-block limit) | if 200, the limit is on the request line alone |
| S1-28…39 | R11 timing | readTags with 25, 50, 100 and ~145 (max that fits) tags, 3 each = 12 | 200 | duration per size |
| S1-38 (optional, last of R11) | POST body size | `POST /cgi/readTags` with a ~5,500-byte body (~220 tags) | unknown | 200 with all records → POST lifts the limit. 408/400/`#E_INVALIDARG` → it does not. **No response within 30 s → stop, log out, health-check** (§7.1). |
| S1-39 (optional) | count limit | readTags `n=250` of the same short tag (`t1..t250=2_Poti1`, ~3.6 KB) | 250 records? | is there a count limit, and how are duplicates handled? |
| S1-50…89 | **R11 reliability** | 10 full passes over the 708 `S_OK` tags (minus GESLO), batched ≤ 3,500-char lines (~5 requests per pass) | identical tag sets | per pass: missing, extra, out-of-order or non-`S_OK` records; HTTP status; duration; value changes |
| S1-90 | logout | `GET /cgi/logout` | `1\n#S_OK` | headers |
| S1-91 | R1: does logout kill the token? | `GET /cgi/readTags?n=1&t1=2_CURRENT_SECOND` with the old cookie | `#E_NEED_LOGIN` (HTTP 200 or 500) | exact body and status |
| S1-92 | R1: logout idempotency | `GET /cgi/logout` with the old cookie | error or `#S_OK` | client logout must tolerate it |
| S1-93 | R1: unauthenticated | `GET /cgi/readTags?n=1&t1=2_CURRENT_SECOND` with no cookie | `#E_NEED_LOGIN` | |

Stop rules specific to Session 1: if S1-02 is not as expected, stop after
logging out. In the R11 steps, an instant 408 is expected; anything else (a slow
408, 5xx, reset) stops the R11 block.

### 7.3 Session 2: R14 readFile block, then events and properties (1 login, about 15–27 requests)

| Step | Purpose | Request | Expect | Record / notes |
|---|---|---|---|---|
| S2-01 | R1 re-login semantics (safe) | `GET /cgi/login?username=admin&password=admin&rnd=<MS>`, **sending the stale cookie from S1** | `#S_OK` + a new token, or `#E_RE-LOGIN_ATTEMPT` | If it returns E_RE-LOGIN_ATTEMPT without a token: S2-02 with the stale cookie shows whether the session was revived. If nothing works: log out (with the stale cookie), then one clean login. |
| S2-02 | sanity | `GET /cgi/readTags?n=1&t1=2_CURRENT_SECOND` | `S_OK` | |

**R14 block.** One file per request, serially. Save every response to
`research/captures/readfile/`. `MODE=ASCII` (fall back to `BINARY` only if the
characters come out garbled). Use GET first; if GET returns `#E_INVALIDARG`, repeat
that step once as POST.

Expected errors are single-line `#E_FAIL`, `#E_INVALIDARG` or `#E_READFORBIDDEN`.
**Unexpected** (stop R14, log out, report): HTTP 5xx, a timeout, `#E_NEED_LOGIN`, a
non-`#` first line, or a size line that does not match the received content.

| Step | Path (justification) | Request |
|---|---|---|
| S2-03 | `workspace/Project/config/alarms.xml` (FTP layout in the old readme + `alarms.html:520`) | `GET /cgi/readFile?MODE=ASCII&PATH=workspace/Project/config/alarms.xml` |
| S2-04 | if S2-03 failed: the absolute variant | `…&PATH=/workspace/Project/config/alarms.xml` |
| S2-05 | if S2-04 failed: the Windows CE variant | `…&PATH=%5Cworkspace%5CProject%5Cconfig%5Calarms.xml` |
| — | If all three fail: **stop R14** and ask the user. They could look up the FTP root, since the old author reached `workspace/Project/config/` by FTP. Do not guess further. | |
| S2-06 | directory listing? (same prefix as the success) | `…&PATH=<prefix>workspace/Project/config/` (one request; any listing then justifies further reads) |
| S2-07 | alarm code → text (`menu_to_field.yaml`: Page109 shows `2_Vrsta_alarma`) | `…&PATH=<prefix>workspace/Project/Page109.jmx` |
| S2-08 | event types for readEvent (`readeventarchive.html:924`) | `…/config/eventconfig.xml` |
| S2-09 | property names (`getsetproperties.html:516`) | `…/config/propertymap.xml` |
| S2-10 | trends (`trend_r.html:1164`) | `…/config/trends.xml` (skip if S1-18 found no trends) |
| S2-11 | groups (`groups_r.html:490`) | `…/config/groups.xml` (skip if S1-17 found no groups) |
| S2-12…14 | At most 3 more files, **each named by a file already read**: a text/message library referenced by `alarms.xml` or `Page109.jmx`, or a file shown by the S2-06 listing. Never a credential/user file. | one per request |

After the R14 block, only if it produced its inputs:

| Step | Purpose | Request | Record |
|---|---|---|---|
| S2-15…17 | R4 history | `GET /cgi/readEvent?eventType=<type from eventconfig.xml>&subType=0&returnTS=true&startTime=<NOW-2592000>&endTime=<NOW>&nEvents=100&deltaTime=0.0&bounds=false`, at most 3 types | lines, text, `S_MOREDATA`? |
| S2-18…20 | R4 paging | the same with `startTime=<last timestamp>` while `S_MOREDATA`, at most 3 pages in total | |
| S2-21 | R3/R5 | `GET /cgi/getProperties?n=<≤10>&it1=<prop>…` with names from propertymap.xml that look like version, serial, MAC or hostname. **Skip names containing pass/pwd/user/login/geslo.** | values (redact) |
| S2-22 | ditto | `browsePropertyGroup?name=<group>&propName=<prop>` / `getPropertyGroup?name=…&gIdName=…&gIdVal=…&n=1&it1=…`, at most 2, only if propertymap.xml defines groups | |
| S2-23 | status | `readIDALStatusParameters?n=<k>&parameterName1=<name>…` only if a file read above names status parameters; otherwise skip | |
| S2-24 | logout | `GET /cgi/logout` | |

### 7.4 Session 3: R1 timing (1 login, ≤ 20 requests, 30 min to about 2.5 h; mostly idle)

No other traffic from us during this session. Each probe is one cheap request,
`GET /cgi/readTags?n=1&t1=2_CURRENT_SECOND`.

1. S3-01 login. S3-02 probe at t = 0.
2. **Keep-alive phase:** a probe every 2 min until t = 20 min (10 probes).
   - All `S_OK` → reads keep the session alive (or the lifetime is > 20 min).
   - `#E_NEED_LOGIN` at t = T → absolute lifetime ≤ T, or idle timeout < 2 min.
     Record it, log out, end the session.
3. **Idle ladder:** wait 3, 5, 8, 12, 17, 23, 30 min between probes (at most 7
   probes). The first `#E_NEED_LOGIN` after gap g with the previous gap g' alive
   means g' < idle timeout ≤ g.
4. S3-end: `GET /cgi/logout`, even after `E_NEED_LOGIN`; record the response to a
   dead token.

Record exact timestamps for every probe. The timeout value also sets the HA client's
re-login policy and the old integration's leaked-slot lifetime.

### 7.5 Session 4 (GATED): slot count, logout frees a slot, second login with a valid token

**Needs the lead's and the user's explicit approval.** It deliberately holds more
than one session at once, which conflicts with the letter of CLAUDE.md ("Never run
two pump sessions at once").

Run it only after Session 3, so the worst-case lockout is known, with Moja Orca
closed, from one serial script, in under a minute.

1. Login A, login B, login C, login D (no cookies), stopping at the first
   `#E_TOO_MANY_USERS`. That `#E_TOO_MANY_USERS` is the measurement: no backoff, no
   retry. The number of `S_OK` logins = free slots.
2. Logout A, then **immediately** login E → `S_OK` means logout frees the slot at
   once.
3. Login F **with B's valid cookie** → `#E_RE-LOGIN_ATTEMPT`? Does B's token still
   work afterwards (one readTags)?
4. `finally`: log out every token still held (B, C, D, E, F if issued).
5. Then one fresh login and logout to prove the pump is accepting logins.

At most 12 requests. Stop: if step 2 returns `E_TOO_MANY_USERS`, logout does **not**
free slots. Log out what you hold, and tell the user that logins may be blocked for
up to the idle timeout.

### 7.6 Budget

| Session | Logins | Requests | Wall time |
|---|---|---|---|
| 1 | 1 | ~95–105 | ~5 min |
| 2 | 1 | ~15–27 | ~2 min |
| 3 | 1 | ≤ 20 | 0.5–2.5 h (idle) |
| 4 (gated, optional) | ≤ 6 | ≤ 12 | < 1 min |
| **Total** | **3 (+≤6 gated)** | **~130–150 (+≤12)** | |

---

## 8. Recommendations for the client (PLAN §7.2)

1. **Batch by bytes, not by tag count.** Build the final request including every
   header (Host, Cookie, User-Agent, Accept, Accept-Encoding) and keep the header
   block ≤ (measured limit − 256 bytes). Until S1-25…27 run, use a request line of
   ≤ 3,500 characters with aiohttp's defaults. Percent-encoding counts. If POST
   proves to be unlimited (S1-38), a single POST per poll is simpler; still keep a
   byte cap.
2. **Treat HTTP 408 as a client bug** (`OrcaProtocolError("request too large")`),
   not as missing tags and not as transient. Split the batch and log loudly. Never
   retry at the same size.
3. **Parse by name and check positions.** Expect exactly N records in request order.
   A missing, duplicated or reordered record is a protocol anomaly: log it and re-read
   only those tags once (PLAN §7.2). Split the value line at the first tab. Decode the
   quality: `qq != 3` → value unavailable (`bad_quality` / `uncertain` reasons).
   `-9999` → `not_connected`.
4. **Check the first line before the records.** A first line `#<CODE>` without a
   tab is a whole-request error that applies to every tag.
5. **Read the body even on HTTP 500.** Map `#E_…` codes when present; HTTP 500
   without a code is transient.
6. Error mapping:

   | Code | Exception / reason | Transient? |
   |---|---|---|
   | `E_NEED_LOGIN` | re-login once (single-flight), retry the request once | yes |
   | `E_TOO_MANY_USERS` | `OrcaTooManyUsersError`; no sleep in the client | yes, but slow |
   | `E_PASS_DONT_MATCH` | `OrcaAuthError` (reauth flow) | no |
   | `E_RE-LOGIN_ATTEMPT` | success if a token is held; otherwise `OrcaProtocolError` (refine after S2-01/S4) | — |
   | `E_UNKNOWNTAG` | per tag, reason `unknown_tag`; stable per firmware; topology treats it as "absent" only after a clean read | no |
   | `E_READFORBIDDEN` | `OrcaTagError`, reason `forbidden` | no |
   | `E_UNACTIVETAG` / `E_INACTIVETAG` | reason `no_response`; retry next poll | yes |
   | `E_FAIL` (per tag or whole request) | reason `no_response` / `OrcaProtocolError` | yes |
   | `E_INVALIDARG` | `OrcaProtocolError` (our bug) | no |
   | `E_TAG_NOT_BOUNDED…`, `E_BOUNDED_TAG_NOT_CONNECTED…` | reason `unknown_tag` (project config) | no |
   | timeouts, resets, connection refused | `OrcaConnectionError` / `OrcaTimeoutError` | yes |

7. **Sessions.**
   - Log in lazily and reuse the token.
   - Do not call login while holding a valid token (`E_RE-LOGIN_ATTEMPT`).
   - Log out on unload and on shutdown, tolerating errors and stale tokens
     (S1-92).
   - If S3 shows that reads keep a session alive, poll at an interval well below
     the idle timeout so the session never dies. Otherwise budget one re-login per
     timeout.
   - Never open a second session for options flows or diagnostics; share the
     client.
8. **One request at a time, a new connection each time** (the server closes it).
   Use a 10–15 s request timeout and no client-side pipelining or keep-alive
   assumptions.
9. **Metadata and alarms come from the project, not from readTags.** Use the
   S1-11/S1-13…16 and R14 results to fill the catalog: ranges, writability, enum and
   alarm texts. Do not call browse in normal polling. If it is useful at all, use
   it once at setup or in diagnostics.
10. **Alarms in HA:**
    - Poll the alarm tags (`2_JE_ALARM`, `2_Vrsta_alarma`, …) with readTags in the
      normal batch.
    - Optionally poll `readAlarms` for the alarm names from browse, which gives
      state and timestamp, with texts from browse or alarms.xml or Page109.jmx at
      setup.
    - Never send `acknowledgeAlarms` or `resetAlarms`.
    - On this pump, `2_NAPAKA`, `2_Alarm_RF1..3` and `2_Cas_zakasn_ALARM_RF1` are
      `E_UNKNOWNTAG` (H: dump).
11. **The emulator** (§7.4 of PLAN) should reproduce:
    - the 4,095-byte header limit with an instant 408 HTML page;
    - `Connection: close`;
    - `#E_NEED_LOGIN` after the idle timeout;
    - `#E_TOO_MANY_USERS` beyond N sessions;
    - `#E_UNKNOWNTAG` without a value line;
    - whole-request `#E_FAIL`;
    - the `1\n#S_OK…` login and logout bodies.

---

## 9. Open questions (could not settle statically)

1. Session slot count, idle timeout, keep-alive by reads, whether logout frees a slot
   at once, and the exact meaning of `E_RE-LOGIN_ATTEMPT` (S1-90…93, S2-01, S3, S4).
2. Whether login sets `Set-Cookie`, and what the leading `1` in login/logout bodies
   means (S1-01).
3. The exact limit (request line vs. header block, 3,990 predicted), and whether POST
   bodies avoid it (S1-25…27, S1-38).
4. Whether the server ignores or uses `client` (S1-03).
5. The format of `browse … returnObject=true`, and whether it carries tag type, access
   mode, EU min/max and alarm descriptions (S1-11, S1-13…16).
6. Whether `hasValue` is a glob or a regex (S1-10).
7. The readFile path root and separator; whether a directory path returns a listing;
   file encoding (Slovenian characters: ASCII vs. BINARY) (S2-03…06).
8. Where JMobile stores alarm texts and multi-language strings: in `alarms.xml`, in
   page `.jmx` message lists, or in a separate text library (S2-07, S2-12…14).
9. Event types in `eventconfig.xml`, and whether readEvent holds an alarm history with
   texts (S2-08, S2-15…20).
10. Status parameter names for `readIDALStatusParameters`, and property names useful
    for identity (serial/version) (S2-21…23).
11. The formats of `getTime`, `getLocalTime`, `getPLCStatus` and the `SA` field of
    `getTCPIPSettings`; whether newer firmware returns a MAC there (S1-05…08).
12. Whether `E_UNACTIVETAG` or `E_INACTIVETAG` is the spelling on this firmware, and
    when it occurs.
13. Whether the "does not always respond with data" behaviour reported for the
    related device also happens here, e.g. around compressor start/stop (S1-50…89;
    longer-term HA diagnostics).
