# G-D reference-label worksheet — CyberGuard v3 (§8.9)

**What this is.** §8.9 requires human-authored gold IOC/entity spans for the 100
pinned documents, independently re-annotated on a 20-document subset, before the G-D
gate can be measured at all. The scorer already exists; this reference does not.

**How to record a span.** For every IOC/entity in a document record its exact
character offsets into the document text, its normalized value, and its type.
Permitted types: `ipv4`, `domain`, `url`, `md5`, `sha1`, `sha256`, `cve`, `filepath`, `registry`, `email`, `mutex`, `other`.

Write into `v3/evals/gd/bundle-A.jsonl` (all 100 documents) with your name in `annotator`.

**Second annotator (blind).** A *different* person must re-annotate the 20 documents
listed in `v3/evals/gd/bundle-B.jsonl` without seeing the first pass. Span-level F1 between the two passes
must be >= 0.90; below that the full set is re-annotated, and disagreements are
adjudicated by a third qualified reviewer with the adjudications recorded.

**Not permitted:** model-drafted spans as a substitute for human annotation.
`--verify` rejects a bundle whose `annotator` names a model.

Then run: `python3 tools/gd_annotation_kit.py --verify`

---

## doc 0 — row_idx 0

```text
Incident Response Summary: On detection of anomalous traffic to 71.227.188.3, the Europol IR team identified Dridex running as C:\Users\admin\Downloads\lsass.dmp. The threat actor, believed to be Velvet Tempest, used Brute Ratel for credential harvesting and Havoc for lateral movement. Exfiltrated data was sent to update-cache.cc and syncauth.link. The initial dropper (MD5: 62472b50f126dc17cca3586b6796feda) was delivered via a phishing email from noreply@secure-verify.net. A second C2 node was observed at 10.42.62.126, with a persistence mechanism writing to /dev/shm/ntds.dit.
```

spans: _(fill in bundle)_

## doc 1 — row_idx 1

```text
A backdoor also known as: Trojan.Downloader.Farfly.L Multi.Threats.InArchive W32/Risk.NCBB-0700 Trojan.Farfli Win.Trojan.Downloader-2275 Trojan.Downloader.Farfly.L Trojan.Downloader.Farfly.L Trojan.Win32.Crypted.dkwpfn Trojan.Win32.Z.Downloader.266845 Trojan.Downloader.Farfly.L Trojan.DownLoader4.59614 Downloader.Selvice.Win32.747 TROJ_DLOADR.SMQ Trojan-Downloader.Win32.Selvice W32/MalwareS.ASNW Trojan.Downloader.Farfly.L TrojanDownloader:Win32/Caxnet.B Worm.WhiteIce Trojan.Downloader.Farfly.L Trojan.Downloader.Farfly.L Trojan.DL.Selvice!qQfZyIPcdpU Win32/Trojan.Downloader.6fb
```

spans: _(fill in bundle)_

## doc 2 — row_idx 2

```text
Forensic Investigation Notes: Analysis of the compromised host revealed Metasploit artifacts at /dev/shm/csrss.exe. Memory dump analysis confirmed execution of Chisel. Registry modifications pointed to persistence via /home/user/.config/csrss.exe. Network forensics identified connections to 159.70.34.15 and storageupdate.link. Email headers traced the initial vector to security@identity-verify.cc. File /usr/local/bin/chrome_helper.exe (MD5: 846560ce3c1096a71b0c9faffc5c7d6e) was identified as the initial dropper. A staging URL hxxps://syncsync.org/wp-content/uploads/doc.php resolved to 104.212.67.224. Secondary artifact hash: MD5: 16bf9a924f6956a8830b5d638fae4124.
```

spans: _(fill in bundle)_

## doc 3 — row_idx 3

```text
There are 3 types of lists recognized by ZxShell : plain ip addresses , HTTP and FTP addresses .
```

spans: _(fill in bundle)_

## doc 4 — row_idx 4

```text
A backdoor also known as: W32.KloggerQKA.Trojan Trojan-Downloader.Win32.Delf!O Backdoor.Gobot Downloader.Delf.Win32.70 Backdoor.W32.Gobot.lfDt Trojan/Downloader.Delf.bm Win32.Trojan.WisdomEyes.16070401.9500.9965 W32/Avokado.SIKN-9031 W32.Gobot.A Backdoor.Gobot Win32/Gobot.B WORM_GOBOT.G Win.Downloader.Delf-144 Trojan.Win32.Delf.gvzc Trojan.Win32.Delf.47087 Win32.HLLW.Ghostbot WORM_GOBOT.G BehavesLike.Win32.Kudj.pc Backdoor.Win32.Gobot W32/Avokado.B@bd TrojanDownloader.Delf.pgr TR/Dldr.Delf.BM Trojan[Backdoor]/Win32.Gobot Backdoor:Win32/Gobot.A Worm/Win32.IRCBot.R29095 Bck/Gotob.AA Trojan.Delf.BM Win32/TrojanDownloader.Delf.BM Trojan.DL.Delf!UOW7nlBxiow
```

spans: _(fill in bundle)_

## doc 5 — row_idx 5

```text
CVE-2025-8893: A maliciously crafted PDF file, when parsed through certain Autodesk products, can force an Out-of-Bounds Write vulnerability. A malicious actor may leverage this vulnerability to cause a crash, cause data corruption, or execute arbitrary code in the context of the current process.
```

spans: _(fill in bundle)_

## doc 6 — row_idx 6

```text
More recent variants blend rooting capabilities and click fraud .
```

spans: _(fill in bundle)_

## doc 7 — row_idx 7

```text
A backdoor also known as: Trojan/W32.ShipUp.90112 W32.VisuDir.A3 Trojan.Zusy.D2CF33 PE_SHIPUP.A Win32.Worm.ShipUp.h Win32/Gamarue.ISACBfC PE_SHIPUP.A Trojan.Win32.ShipUp.futk TrojWare.Win32.ShipUp.AR Trojan.KillFiles.28137 Worm.Win32.ShipUp Worm:Win32/Lecna.A!dha Trojan.Win32.ShipUp.futk Trojan/Win32.Cossta.R120893 Trojan.FakeDoc Trojan.Win32.Csyr.A
```

spans: _(fill in bundle)_

## doc 8 — row_idx 8

```text
ApostropheCMS is an open-source Node.js content management system. Versions 4.28.0 and prior contain a stored cross-site scripting vulnerability in the @apostrophecms/color-field module, where color values prefixed with -- bypass TinyColor validation intended for CSS custom properties, and the launder.string() call performs only type coercion without stripping HTML metacharacters. These unsanitized values are then concatenated directly into <style> tags both in per-widget style elements rendered for all visitors and in the global stylesheet rendered for editors, with the output marked as safe HTML. An editor can inject a value which closes the style tag and executes arbitrary JavaScript in the browser of every visitor to any page containing the affected widget. This enables mass session hijacking, cookie theft, and privilege escalation to administrative control if an admin views draft content. This issue has been fixed in version 4.29.0.
```

spans: _(fill in bundle)_

## doc 9 — row_idx 9

```text
Definition of populateConfigMap , which loads the map with values Correlating the last two steps , one can observe that the malware payload receives the configuration for the following properties : number – The default number to be send to the server ( in case the number is not available from the device ) api – The API key url – The URL to be used in WebView to display on the ransom note The malware saves this configuration to the shared preferences of the app data and then it sets up all the Broadcast Receivers . There are many articles and researches online about APT15 and their activities , the most recent one by NCC Group . WinZip version 11.2 and 24.0, and the built-in unzIP S-TOOL tool in Windows , recognized that the attachment SHIPPING_MX00034900_PL_INV_pdf[ . ]zip is an invalid . The threat actor first detected towards the end of last year when it attacked at least 87 organizations around the world in two months ' time .
```

spans: _(fill in bundle)_

## doc 10 — row_idx 10

```text
QuickMute is a malware developed using the C/C++ programming language. Functionally provides download, RC4 decryption, and in-memory launch of the payload (waiting for a PE file with the export function "HttpsVictimMain"). To communicate with the management server, a number of protocols are provided, in particular: TCP, UDP, HTTP, HTTPS.
```

spans: _(fill in bundle)_

## doc 11 — row_idx 11

```text
Exbyte is an exfiltration tool written in Go that is uniquely associated with BlackByte operations. Observed since 2022, Exbyte transfers collected files to online file sharing and hosting services.
```

spans: _(fill in bundle)_

## doc 12 — row_idx 12

```text
In the Linux kernel, the following vulnerability has been resolved:

thermal/drivers/cpufreq_cooling: Fix slab OOB issue

Slab OOB issue is scanned by KASAN in cpu_power_to_freq().
If power is limited below the power of OPP0 in EM table,
it will cause slab out-of-bound issue with negative array
index.

Return the lowest frequency if limited power cannot found
a suitable OPP in EM table to fix this issue.

Backtrace:
[<ffffffd02d2a37f0>] die+0x104/0x5ac
[<ffffffd02d2a5630>] bug_handler+0x64/0xd0
[<ffffffd02d288ce4>] brk_handler+0x160/0x258
[<ffffffd02d281e5c>] do_debug_exception+0x248/0x3f0
[<ffffffd02d284488>] el1_dbg+0x14/0xbc
[<ffffffd02d75d1d4>] __kasan_report+0x1dc/0x1e0
[<ffffffd02d75c2e0>] kasan_report+0x10/0x20
[<ffffffd02d75def8>] __asan_report_load8_noabort+0x18/0x28
[<ffffffd02e6fce5c>] cpufreq_power2state+0x180/0x43c
[<ffffffd02e6ead80>] power_actor_set_power+0x114/0x1d4
[<ffffffd02e6fac24>] allocate_power+0xaec/0xde0
[<ffffffd02e6f9f80>] power_allocator_throttle+0x3ec/0x5a4
[<ffffffd02e6ea888>] handle_thermal_trip+0x160/0x294
[<ffffffd02e6edd08>] thermal_zone_device_check+0xe4/0x154
[<ffffffd02d351cb4>] process_one_work+0x5e4/0xe28
[<ffffffd02d352f44>] worker_thread+0xa4c/0xfac
[<ffffffd02d360124>] kthread+0x33c/0x358
[<ffffffd02d289940>] ret_from_fork+0xc/0x18
```

spans: _(fill in bundle)_

## doc 13 — row_idx 13

```text
A backdoor also known as: JS/Iframe.DGS Script.Trojan-Downloader.IFrame.AE Trojan-Downloader.JS.Iframe.deg Trojan.Script.Expack.bvtkmp PDF.DownLoader.3 BehavesLike.PDF.BadFile.db JS/BlacoleRef.CZ.29 Trojan[Downloader]/JS.Iframe.deg Trojan-Downloader.JS.Iframe.deg JS/Moat.241E54F!tr
```

spans: _(fill in bundle)_

## doc 14 — row_idx 14

```text
Artifact Analysis for Latrodectus campaign:
Stage 1 dropper at /etc/cron.d/implant.so - SHA256: accc7052c902d2b2636309be15d3d4d65bffd2583e1456d80074bea4275ffe18
Stage 2 loader at C:\Users\admin\Desktop\runtime.dll - SHA1: 40ead3e906eb0e2d3667075fce34060da216fc36
Final payload at /opt/app/bin/chrome_helper.exe - SHA256: 9d42da2cf1008f90ad71e252067f2f239638d30efe596392c79306fc20401037
Exfiltration module - SHA1: a4ff088fcaf108d69fa820b8bad648710ffd7e85
All stages communicated with 90.231.28.94. Havoc signatures detected in Stage 2.
```

spans: _(fill in bundle)_

## doc 15 — row_idx 15

```text
A backdoor also known as: Trojan.VBS.UAJ Trojan.VBS.UAJ Win32.Trojan.WisdomEyes.16070401.9500.9853 Trojan.VBS.UAJ Vbs.Trojan.Vbs.Ljjs Trojan.VBS.UAJ Trojan.VBS.UAJ Trojan.DownLoader19.25627 BehavesLike.Win32.Downloader.qh Trojan.Barys Trojan.MSIL.amcc Trojan.VBS.UAJ Trojan.VBS.UAJ Trojan.MSIL.Zapchast VBS/Shutdown.NAH
```

spans: _(fill in bundle)_

## doc 16 — row_idx 16

```text
Vulnerability Advisory: CVE-2023-39714 is a critical race condition affecting Windows 11. SentinelOne confirmed active exploitation by Storm-0558 in the wild. Exploitation delivers RemcosRAT (SHA1: fe45c5659a9c6ddcaad6797958a6154e98cc6fe9) which is dropped to /var/tmp/ntds.dit. The exploit payload is hosted at http://data-static.io/wp-content/uploads/doc.php and communicates to 10.242.40.109 for C2.
```

spans: _(fill in bundle)_

## doc 17 — row_idx 17

```text
The real C & C address is encoded in the Twitter names , and can only be revealed once decoded . FireEye believes the change from RIPTIDE to HIGHTIDE represents a temporary tool shift to decrease malware detection while APT12 developed a completely new malware toolset . Below is a list of AdrGen . Mandiant used these signatures to search the XPdb for additional attacker payloads that were deleted by the threat actor or otherwise unable to be identified through other forms of analysis .
```

spans: _(fill in bundle)_

## doc 18 — row_idx 18

```text
InvisibleFerret is a modular python malware that is leveraged for data exfiltration and remote access capabilities.   InvisibleFerret consists of four modules: main, payload, browser, and AnyDesk.  InvisibleFerret malware has been leveraged by North Korea-affiliated threat actors identified as DeceptiveDevelopment or Contagious Interview since 2023.  InvisibleFerret has historically been introduced to the victim environment through the use of the BeaverTail malware.
```

spans: _(fill in bundle)_

## doc 19 — row_idx 19

```text
Once the file has been downloaded and executed , the new process will launch a legitimate executable , such as “ msiexec.exe ” , and inject code into it .
```

spans: _(fill in bundle)_

## doc 20 — row_idx 20

```text
Artifact Analysis for Gootloader campaign:
Stage 1 dropper at /var/tmp/loader.exe - SHA256: 0a05928a49b4a37219ddd89de71269ec113beed92be59803be9b5f08fcaccd47
Stage 2 loader at C:\Users\admin\Downloads\loader.exe - SHA1: 72f3968e91bcc323136dd30d85ae887382c487e2
Final payload at /etc/cron.d/update.dll - SHA1: 346f216583a1460bb97ebeee0e67f852d9770a45
Exfiltration module - MD5: f6c75c26890bae32e785b3c16b1dda08
All stages communicated with 37.237.169.1. Metasploit signatures detected in Stage 2.
```

spans: _(fill in bundle)_

## doc 21 — row_idx 21

```text
ARS Loader, also known as ARS VBS Loader, is written in Visual Basic Script and its main purpose is to control an infected machine via different available commands, acting as a remote access trojan (RAT). Its code is based on ASPC, another Visual Basic Script malware, which at the same time seems to be based on SafeLoader.
```

spans: _(fill in bundle)_

## doc 22 — row_idx 22

```text
Incident Response Summary: On detection of anomalous traffic to 22.5.240.35, the INTERPOL IR team identified BumbleBee running as C:\Users\admin\AppData\Local\Temp\winlogon.exe. The threat actor, believed to be BlackTech, used BITSAdmin for credential harvesting and PowerView for lateral movement. Exfiltrated data was sent to gatewaystatic.info and auth-edge.com. The initial dropper (MD5: 12678ee09fd6fc46d98e530426bdbdb0) was delivered via a phishing email from report@phishing-domain.com. A second C2 node was observed at 178.203.108.183, with a persistence mechanism writing to /var/tmp/beacon.dll.
```

spans: _(fill in bundle)_

## doc 23 — row_idx 23

```text
Vulnerability in the Oracle One-to-One Fulfillment product of Oracle E-Business Suite (component: Print Server). Supported versions that are affected are 12.1.1-12.1.3 and 12.2.3-12.2.9. Easily exploitable vulnerability allows unauthenticated attacker with network access via HTTP to compromise Oracle One-to-One Fulfillment. Successful attacks require human interaction from a person other than the attacker and while the vulnerability is in Oracle One-to-One Fulfillment, attacks may significantly impact additional products. Successful attacks of this vulnerability can result in unauthorized access to critical data or complete access to all Oracle One-to-One Fulfillment accessible data as well as unauthorized update, insert or delete access to some of Oracle One-to-One Fulfillment accessible data. CVSS 3.0 Base Score 8.2 (Confidentiality and Integrity impacts). CVSS Vector: (CVSS:3.0/AV:N/AC:L/PR:N/UI:R/S:C/C:H/I:L/A:N).
```

spans: _(fill in bundle)_

## doc 24 — row_idx 24

```text
A backdoor also known as: Win32.Wurmark.A@mm Win32.Wurmark.A@mm W32/Mugly.h@MM W32.W.Wurmark.g!c W32/Wurmark.g Win32.Wurmark.A@mm Win32.Wurmark.E90817 I-Worm.Wurmark!utsCc3R91ZU W32/Wurmark.F W32.Mugly.G@mm Win32/Wurmark.G WORM_MUGLY.H Worm.Wurmark.G Email-Worm.Win32.Wurmark.g Trojan.Win32.Wurmark.fsml Virus.Win32.Heur.c Win32.Wurmark.A@mm Worm.Win32.Wurmark.G Win32.Wurmark.A@mm Worm.Wurmark.Win32.11 WORM_MUGLY.H BehavesLike.Win32.VBObfus.fc W32/Wurmark.JPAN-1543 I-Worm.Wurmark.a WORM/Uglatad.2 Worm[Email]/Win32.Wurmark Worm:Win32/Mugly.H@mm Win32/Mugly.worm.351744 Win32.Wurmark.A@mm Win32/Mugly.G Worm.Wurmark Win32.Wurmark.A@mm Virus.Win32.QQRob.AS W32/Mugly.H@mm I-Worm/Wurmark.E Worm.Win32.Wurmark.AGmW
```

spans: _(fill in bundle)_

## doc 25 — row_idx 25

```text
It turned out that they are also atypical by many means.
```

spans: _(fill in bundle)_

## doc 26 — row_idx 26

```text
ZxFunction002 This will either bind the calling process to a port or has the calling process connect to a remote host .
```

spans: _(fill in bundle)_

## doc 27 — row_idx 27

```text
A backdoor also known as: Backdoor/W32.SdBot.25088.Q Backdoor/Afbot.a BKDR_POEBOT.DK Win32.Trojan.WisdomEyes.16070401.9500.9999 Backdoor.Trojan BKDR_POEBOT.DK Backdoor.Win32.Afbot.a Trojan.Win32.Afbot.daze Backdoor.Win32.S.Afbot.25088 Backdoor.W32.Afbot.a!c Backdoor.Win32.Afbot.~A BackDoor.IRC.Afbot Backdoor.Afbot.Win32.1 Backdoor/Afbot.a Trojan[Backdoor]/Win32.Afbot Backdoor:Win32/Afbot.A Backdoor.Win32.Afbot.a Backdoor.Afbot Bck/Iroffer[.]BG Win32.Backdoor.Afbot.Szbp Backdoor.Afbot!ktevPrMqQWw W32/Afbot.A!tr.bdr Win32/Backdoor.BO.3c4
```

spans: _(fill in bundle)_

## doc 28 — row_idx 28

```text
IOC Bulletin - Gootloader Campaign:
Network Indicators:
- 183.148.21.61
- 7.227.211.153
- 89.180.107.95
- nodenode.net
- node-login.top
URLs:
- http://storagebackup.online/admin/config
- hxxp://proxysync.tech/secure/token
Email Senders:
- finance@secure-verify.net
- noreply@login-portal.tech
File Indicators:
- SHA256: c6a1a61ccf9355019618d9098e7293a52705eb1970671a17610cb5cbbde47463
- MD5: cd3c9442c3b22cf36a91fa3c2528dfb1
- Drop path: C:\Windows\Tasks\payload.bin
```

spans: _(fill in bundle)_

## doc 29 — row_idx 29

```text
PANW Unit 42 describes this malware as capable of up and downloading files as well as loading additional shellcode payloads into selected target processes. It uses the Microsoft Graph API and Dropbox API as C&C channel.
```

spans: _(fill in bundle)_

## doc 30 — row_idx 30

```text
In December 2012 Mofang started a campaign against a new target , called ' seg ' for the purpose of this report .
```

spans: _(fill in bundle)_

## doc 31 — row_idx 31

```text
so TAU is looking for newer versions ANEL samples .
```

spans: _(fill in bundle)_

## doc 32 — row_idx 32

```text
The next most common is port 53 .
```

spans: _(fill in bundle)_

## doc 33 — row_idx 33

```text
A backdoor also known as: Win32.Trojan.WisdomEyes.16070401.9500.9962 Trojan.Win32.Graftor.dcgcrd TrojWare.Win32.Kryptik.~NT Trojan-Downloader.Win32.Banload Trojan:Win32/BrobanAda.A TScope.Trojan.Delf
```

spans: _(fill in bundle)_

## doc 34 — row_idx 34

```text
BanPolMex is a remote access trojan that uses TCP for communication.

It uses an RC4-like stream cipher called Spritz for encryption of its configuration and network traffic.

It sends detailed information about the victim's environment, like computer name, Windows version, free space of memory and all drives, processor identifier and architecture, system locale, system metrics, manufacturer, and network configuration.

It supports almost 30 commands that include operations on the victim’s filesystem, basic process management, file exfiltration, and the download and execution of additional tools from the attacker’s C&C server. As in many RATs from Lazarus arsenal, the commands are indexed by 32-bit integers. However, in this case the indicis are convertible into a meaningful ASCII representation, that even suggests the functionality: SLEP, HIBN, DRIV, DIR, DIRP, CHDR, RUN, RUNX, DEL, WIPE, MOVE, FTIM, NEWF, DOWN, ZDWN, UPLD, PVEW, PKIL, CMDL, DIE, GCFG, SCFG, TCON, PEEX, PEIN.

It has aclui.dll as the internal DLL name. It contains statically linked code from open-source libraries like libcurl (version 7.47.1) or zLib (version 0.15).

BanPolMex RAT was delivered for victims of a watering hole campaign targeting employees of Polish and Mexican banks, that was discovered in February 2017. It is usually loaded by HOTWAX.
```

spans: _(fill in bundle)_

## doc 35 — row_idx 35

```text
In a separate incident , CTU researchers identified a file named s.txt , which is consistent with the output of the Netview host-enumeration tool .
```

spans: _(fill in bundle)_

## doc 36 — row_idx 36

```text
FakeSpy Chunghwa Post version installation process and application UI . Bitdefender’s investigation shows the attackers’ main methods remain to quietly infiltrate the infrastructure by establishing a foothold on an employee’s system , then move laterally across the infrastructure or elevate privileges to find critical systems that manage financial transactions or ATM networks . Ultimately , this lead us to the conclusion that several of Gorgon Group 's members have a nexus in Pakistan .
```

spans: _(fill in bundle)_

## doc 37 — row_idx 37

```text
A backdoor also known as: NetTool.Tor Backdoor.Bot Tool.Tor.Win32.4 Win32.Trojan.WisdomEyes.16070401.9500.9989 Backdoor.Trojan not-a-virus:NetTool.Win32.Tor.f Trojan.Win32.MLW.dbcsxd Trojan.DownLoader8.56801 Sefnit.ag W32/Trojan.OTFO-7506 HackTool[NetTool]/Win32.Tor TrojanDropper:Win32/Sefnit.A not-a-virus:NetTool.Win32.Tor.f TrojanDropper.Sefnit Riskware.NetTool! Win32/Trojan.07c
```

spans: _(fill in bundle)_

## doc 38 — row_idx 38

```text
delivery : to deliver specified text to all victim ’ s contacts ( SMS worming ) .
```

spans: _(fill in bundle)_

## doc 39 — row_idx 39

```text
The earliest evidence obtained shows it has been in use since at least November 2016.
```

spans: _(fill in bundle)_

## doc 40 — row_idx 40

```text
A backdoor also known as: Trojan.Win32.PopUpper!O Worm.Shamli.A3 Trojan.PopUpper.Win32.66 Trojan.ShellStartup.E6CAF2 Win32.Trojan.WisdomEyes.16070401.9500.9949 Trojan.Win32.PopUpper.eg W32.Virut.low6 Trojan.MulDrop3.38938 BehavesLike.Win32.VBObfus.tz Trojan/PopUpper.bi Trojan/Win32.PopUpper Worm:Win32/Shamli.A Trojan.Win32.A.PopUpper.1695744 Trojan.Win32.PopUpper.eg Trojan/Win32.PopUpper.R52146 MAS.Trojan.VB.0879 Win32/VB.ODX Trojan.Win32.PopUpper W32/Popupper.A!tr Trj/Shamli.A Win32/Trojan.41d
```

spans: _(fill in bundle)_

## doc 41 — row_idx 41

```text
This and following versions were masquerading as fake “ Adobe Flash Player ” apps . The OSB functions as the interface between CIA operational staff and the relevant technical support staff . CopyKittens is an Iranian cyber espionage group that has been operating since at least 2013 .
```

spans: _(fill in bundle)_

## doc 42 — row_idx 42

```text
In the Linux kernel, the following vulnerability has been resolved:

nvmem: Fix shift-out-of-bound (UBSAN) with byte size cells

If a cell has 'nbits' equal to a multiple of BITS_PER_BYTE the logic

 *p &= GENMASK((cell->nbits%BITS_PER_BYTE) - 1, 0);

will become undefined behavior because nbits modulo BITS_PER_BYTE is 0, and we
subtract one from that making a large number that is then shifted more than the
number of bits that fit into an unsigned long.

UBSAN reports this problem:

 UBSAN: shift-out-of-bounds in drivers/nvmem/core.c:1386:8
 shift exponent 64 is too large for 64-bit type 'unsigned long'
 CPU: 6 PID: 7 Comm: kworker/u16:0 Not tainted 5.15.0-rc3+ #9
 Hardware name: Google Lazor (rev3+) with KB Backlight (DT)
 Workqueue: events_unbound deferred_probe_work_func
 Call trace:
  dump_backtrace+0x0/0x170
  show_stack+0x24/0x30
  dump_stack_lvl+0x64/0x7c
  dump_stack+0x18/0x38
  ubsan_epilogue+0x10/0x54
  __ubsan_handle_shift_out_of_bounds+0x180/0x194
  __nvmem_cell_read+0x1ec/0x21c
  nvmem_cell_read+0x58/0x94
  nvmem_cell_read_variable_common+0x4c/0xb0
  nvmem_cell_read_variable_le_u32+0x40/0x100
  a6xx_gpu_init+0x170/0x2f4
  adreno_bind+0x174/0x284
  component_bind_all+0xf0/0x264
  msm_drm_bind+0x1d8/0x7a0
  try_to_bring_up_master+0x164/0x1ac
  __component_add+0xbc/0x13c
  component_add+0x20/0x2c
  dp_display_probe+0x340/0x384
  platform_probe+0xc0/0x100
  really_probe+0x110/0x304
  __driver_probe_device+0xb8/0x120
  driver_probe_device+0x4c/0xfc
  __device_attach_driver+0xb0/0x128
  bus_for_each_drv+0x90/0xdc
  __device_attach+0xc8/0x174
  device_initial_probe+0x20/0x2c
  bus_probe_device+0x40/0xa4
  deferred_probe_work_func+0x7c/0xb8
  process_one_work+0x128/0x21c
  process_scheduled_works+0x40/0x54
  worker_thread+0x1ec/0x2a8
  kthread+0x138/0x158
  ret_from_fork+0x10/0x20

Fix it by making sure there are any bits to mask out.
```

spans: _(fill in bundle)_

## doc 43 — row_idx 43

```text
A backdoor also known as: TROJ_KREP.D Trojan.DownLoad3.10695 Trojan.Swisyn.Win32.8140 TROJ_KREP.D Trojan/Swisyn.jnt Trojan:Win32/Trixpi.A Trojan-Downloader.win32.Delf.xoq W32/Mdrop.CQO!tr Trojan.Win32.Trixpi.A
```

spans: _(fill in bundle)_

## doc 44 — row_idx 44

```text
http : //www.himobilephone [ . While investigating a 2016 intrusion , Secureworks incident responders identified BRONZE BUTLER exploiting a then-unpatched remote code execution vulnerability ( CVE-2016-7836 ) in SKYSEA Client View , a popular Japanese product used to manage an organization . Seedworm then uses open-source tools such as LaZagne and Crackmapexec to obtain Windows authorization credentials .
```

spans: _(fill in bundle)_

## doc 45 — row_idx 45

```text
AllaKore is a simple Remote Access Tool written in Delphi, first observed in 2015 but still in early stages of development. It implements the RFB protocol which uses frame buffers and thus is able to send back only the changes of screen frames to the controller, speeding up the transport and visualization control.
```

spans: _(fill in bundle)_

## doc 46 — row_idx 46

```text
In 2016 , Group-IB identified 10 attacks conducted by MoneyTaker , 6 attacks on banks in the US , 1 attack on a US service provider , 1 attack on a bank in the UK and 2 attacks on Russian banks .
```

spans: _(fill in bundle)_

## doc 47 — row_idx 47

```text
A backdoor also known as: Riskware.Win32.MyBeeSearch.euqqpm Adware.Mybeesearch.17920 Adware.MyBeeSearch.Win32.35 W32/Trojan.ZETF-8401 ADWARE/MyBeeSearch.yttss Adware.BeeSearch/Variant Trj/GdSda.A Msil.Adware.Mybeesearch.Ednu PUA.MyBeeSearch! AdWare.MSIL.Mybeesearch
```

spans: _(fill in bundle)_

## doc 48 — row_idx 48

```text
Both of these libraries are runtime libraries related to Dalvik and ART runtime environments .
```

spans: _(fill in bundle)_

## doc 49 — row_idx 49

```text
A backdoor also known as: Virus.W32.Virus!c Trojan/Spy.KeyLogger.au Trojan.Raw.KeyLog.epwywq BehavesLike.Win32.Cutwail.tc Trojan.Shelma.bbh Trojan/Win32.Shelma Trojan:Win32/Ronohu.A Trj/CI.A Python/Spy.KeyLogger.V Trojan.Python.Spy Python/KeyLogger.V!tr.spy
```

spans: _(fill in bundle)_

## doc 50 — row_idx 50

```text
The iOS malware that is installed over USB by osx.wirelurker
```

spans: _(fill in bundle)_

## doc 51 — row_idx 51

```text
In the Linux kernel, the following vulnerability has been resolved:

arm64: ftrace: fix module PLTs with mcount

Li Huafei reports that mcount-based ftrace with module PLTs was broken
by commit:

  a6253579977e4c6f ("arm64: ftrace: consistently handle PLTs.")

When a module PLTs are used and a module is loaded sufficiently far away
from the kernel, we'll create PLTs for any branches which are
out-of-range. These are separate from the special ftrace trampoline
PLTs, which the module PLT code doesn't directly manipulate.

When mcount is in use this is a problem, as each mcount callsite in a
module will be initialized to point to a module PLT, but since commit
a6253579977e4c6f ftrace_make_nop() will assume that the callsite has
been initialized to point to the special ftrace trampoline PLT, and
ftrace_find_callable_addr() rejects other cases.

This means that when ftrace tries to initialize a callsite via
ftrace_make_nop(), the call to ftrace_find_callable_addr() will find
that the `_mcount` stub is out-of-range and is not handled by the ftrace
PLT, resulting in a splat:

| ftrace_test: loading out-of-tree module taints kernel.
| ftrace: no module PLT for _mcount
| ------------[ ftrace bug ]------------
| ftrace failed to modify
| [<ffff800029180014>] 0xffff800029180014
|  actual:   44:00:00:94
| Initializing ftrace call sites
| ftrace record flags: 2000000
|  (0)
|  expected tramp: ffff80000802eb3c
| ------------[ cut here ]------------
| WARNING: CPU: 3 PID: 157 at kernel/trace/ftrace.c:2120 ftrace_bug+0x94/0x270
| Modules linked in:
| CPU: 3 PID: 157 Comm: insmod Tainted: G           O       6.0.0-rc6-00151-gcd722513a189-dirty #22
| Hardware name: linux,dummy-virt (DT)
| pstate: 60000005 (nZCv daif -PAN -UAO -TCO -DIT -SSBS BTYPE=--)
| pc : ftrace_bug+0x94/0x270
| lr : ftrace_bug+0x21c/0x270
| sp : ffff80000b2bbaf0
| x29: ffff80000b2bbaf0 x28: 0000000000000000 x27: ffff0000c4d38000
| x26: 0000000000000001 x25: ffff800009d7e000 x24: ffff0000c4d86e00
| x23: 0000000002000000 x22: ffff80000a62b000 x21: ffff8000098ebea8
| x20: ffff0000c4d38000 x19: ffff80000aa24158 x18: ffffffffffffffff
| x17: 0000000000000000 x16: 0a0d2d2d2d2d2d2d x15: ffff800009aa9118
| x14: 0000000000000000 x13: 6333626532303830 x12: 3030303866666666
| x11: 203a706d61727420 x10: 6465746365707865 x9 : 3362653230383030
| x8 : c0000000ffffefff x7 : 0000000000017fe8 x6 : 000000000000bff4
| x5 : 0000000000057fa8 x4 : 0000000000000000 x3 : 0000000000000001
| x2 : ad2cb14bb5438900 x1 : 0000000000000000 x0 : 0000000000000022
| Call trace:
|  ftrace_bug+0x94/0x270
|  ftrace_process_locs+0x308/0x430
|  ftrace_module_init+0x44/0x60
|  load_module+0x15b4/0x1ce8
|  __do_sys_init_module+0x1ec/0x238
|  __arm64_sys_init_module+0x24/0x30
|  invoke_syscall+0x54/0x118
|  el0_svc_common.constprop.4+0x84/0x100
|  do_el0_svc+0x3c/0xd0
|  el0_svc+0x1c/0x50
|  el0t_64_sync_handler+0x90/0xb8
|  el0t_64_sync+0x15c/0x160
| ---[ end trace 0000000000000000 ]---
| ---------test_init-----------

Fix this by reverting to the old behaviour of ignoring the old
instruction when initialising an mcount callsite in a module, which was
the behaviour prior to commit a6253579977e4c6f.
```

spans: _(fill in bundle)_

## doc 52 — row_idx 52

```text
An interesting part of the script is the continuous killing of every “ rundll32.exe ” process running into the victim machine , generates a huge amount of noise , as visible in the following process explorer view .
```

spans: _(fill in bundle)_

## doc 53 — row_idx 53

```text
Note that the 104.168.167.16 server is used as a C2 server .
```

spans: _(fill in bundle)_

## doc 54 — row_idx 54

```text
HyperBro is a custom in-memory backdoor used by Threat Group-3390.
```

spans: _(fill in bundle)_

## doc 55 — row_idx 55

```text
An individual who goes by the name LZX in some online forums is believed to be the original author of ZxShell .
```

spans: _(fill in bundle)_

## doc 56 — row_idx 56

```text
A command injection vulnerability in tcpdump command processing on Juniper Networks Junos OS Evolved allows an attacker with authenticated CLI access to be able to bypass configured access protections to execute arbitrary shell commands within the context of the current user. The vulnerability allows an attacker to bypass command authorization restrictions assigned to their specific user account and execute commands that are available to the privilege level for which the user is assigned. For example, a user that is in the super-user login class, but restricted to executing specific CLI commands could exploit the vulnerability to execute any other command available to an unrestricted admin user. This vulnerability does not increase the privilege level of the user, but rather bypasses any CLI command restrictions by allowing full access to the shell. This issue affects Juniper Networks Junos OS Evolved: All versions prior to 20.3R2-S1-EVO; 20.4 versions prior to 20.4R2-S2-EVO; 21.1 versions prior to 21.1R2-EVO; 21.2 versions prior to 21.2R1-S1-EVO, 21.2R2-EVO.
```

spans: _(fill in bundle)_

## doc 57 — row_idx 57

```text
A backdoor also known as: Win32.Trojan.WisdomEyes.16070401.9500.9894 Trojan.Win32.CsDown.bdcfvq Trojan.CsDown.25 TrojanDropper:Win32/Waltrodock.B Trojan.Graftor.D4ACD Trojan.CsNowDown!qDe+BhsdQ1Y W32/WDockDrp.A!tr Trj/CI.A Win32/Trojan.8ea
```

spans: _(fill in bundle)_

## doc 58 — row_idx 58

```text
Google TAG published a threat intelligence report linking Lazarus Group to a new campaign exploiting CVE-2025-17185 in Progress Telerik. The attackers deployed XLoader via Ligolo, establishing C2 communication with 80.170.101.183 and authrelay.info. A secondary payload was downloaded from hxxp://proxydata.xyz/collect. The malware binary (MD5: c8a0f2bb3478669ef6656e5410cab7d9) was dropped to /etc/cron.d/lsass.dmp. Phishing emails were sent from security@auth-check.org targeting enterprise users. A backup C2 server was identified at 172.67.47.209.
```

spans: _(fill in bundle)_

## doc 59 — row_idx 59

```text
Ben Baker , Edmund Brumaghin and Jonah Samost of Talos have a fantastic write-up of this process here .
```

spans: _(fill in bundle)_

## doc 60 — row_idx 60

```text
Although we have only observed APT33 use DROPSHOT to deliver TURNEDUP , we have identified multiple DROPSHOT samples in the wild that delivered wiper malware we call SHAPESHIFT .
```

spans: _(fill in bundle)_

## doc 61 — row_idx 61

```text
Incident Response Summary: On detection of anomalous traffic to 192[.]227[.]43[.]207, the NCSC IR team identified TrickBot running as C:\Users\admin\Desktop\backdoor.elf. The threat actor, believed to be FIN11, used GhostPack for credential harvesting and SharpHound for lateral movement. Exfiltrated data was sent to storage-gateway[.]org and updatenode[ . ]tech. The initial dropper (SHA256: 3efdb9dbe144dc9e664bbbfcfc5ebf2efb9b49ceb24a0c93791075f1b0dacc46) was delivered via a phishing email from security@mail-service[ . ]info. A second C2 node was observed at 103 [ . ] 23 [ . ] 251 [ . ] 221, with a persistence mechanism writing to C:\ProgramData\taskhost.exe.
```

spans: _(fill in bundle)_

## doc 62 — row_idx 62

```text
] infoacount-manager [ .
```

spans: _(fill in bundle)_

## doc 63 — row_idx 63

```text
According to Mandiant, PINEFLOWER is an Android malware family capable of a wide range of backdoor functionality, including stealing system inform information, logging and recording phone calls, initiating audio recordings, reading SMS inboxes and sending SMS messages. The malware also has features to facilitate device location tracking, deleting, downloading, and uploading files, reading connectivity state, speed, and activity, and toggling Bluetooth, Wi-Fi, and mobile data settings.
```

spans: _(fill in bundle)_

## doc 64 — row_idx 64

```text
A backdoor also known as: Win32.Trojan.WisdomEyes.16070401.9500.9982 Trojan.Win32.Dwn.eenglt Win32.Trojan.Spy.Peqf Trojan.DownLoader14.35508 BehavesLike.Win32.HToolMimiKatz.dc Trojan.Symmi.D8341 PWS:Win32/Banker.UC!bit Trj/CI.A
```

spans: _(fill in bundle)_

## doc 65 — row_idx 65

```text
FBI published a threat intelligence report linking MuddyWater to a new campaign exploiting CVE-2022-22601 in Microsoft Exchange. The attackers deployed Conti via Sharphound, establishing C2 communication with 91.136.216.71 and nodenode.live. A secondary payload was downloaded from https://proxy-edge.top/gate.php. The malware binary (SHA1: 0f0ec49fd17b62e62b6c35e417e9756267929e69) was dropped to /etc/cron.d/chrome_helper.exe. Phishing emails were sent from billing@credential-check.site targeting enterprise users. A backup C2 server was identified at 10.190.176.116.
```

spans: _(fill in bundle)_

## doc 66 — row_idx 66

```text
The Callisto Group is an advanced threat actor whose known targets include military personnel, government officials, think tanks, and journalists in Europe and the South Caucasus.
```

spans: _(fill in bundle)_

## doc 67 — row_idx 67

```text
PlushDaemon is a China-aligned APT group that has conducted cyberespionage operations against targets in China, Taiwan, Hong Kong, South Korea, the United States, and New Zealand. They executed a supply chain attack on the South Korean VPN provider IPany, compromising its installer to deploy the SlowStepper backdoor, which features a toolkit of over 30 components. PlushDaemon primarily gains initial access by hijacking legitimate updates of Chinese applications and has also exploited vulnerabilities in legitimate web servers. Additionally, they have utilized the Visual Studio command line utility regcap.exe to side-load a malicious DLL named lregdll.dll.
```

spans: _(fill in bundle)_

## doc 68 — row_idx 68

```text
In August 2015 , the admin@338 sent spear phishing emails to a number of Hong Kong-based media organizations , including newspapers , radio , and television .
```

spans: _(fill in bundle)_

## doc 69 — row_idx 69

```text
Valak is a multi-stage modular malware that can function as a standalone information stealer or downloader, first observed in 2019 targeting enterprises in the US and Germany.
```

spans: _(fill in bundle)_

## doc 70 — row_idx 70

```text
DarkKomet is a freeware remote access trojan that was released by an independent software developer.
```

spans: _(fill in bundle)_

## doc 71 — row_idx 71

```text
A longstanding cyberespionage campaign has been targeting mainly Japanese organizations with its own, custom-developed, malware Backdoor.Daserf.
```

spans: _(fill in bundle)_

## doc 72 — row_idx 72

```text
NATS-Server is a High-Performance server for NATS[ . ]io, a cloud and edge native messaging system. Prior to versions 2.11.15 and 2.12.6, when using mTLS for client identity, with `verify_and_map` to derive a NATS identity from the client certificate's Subject DN, certain patterns of RDN would not be correctly enforced, allowing for authentication bypass. This does require a valid certificate from a CA already trusted for client certificates, and `DN` naming patterns which the NATS maintainers consider highly unlikely. So this is an unlikely attack. Nonetheless, administrators who have been very sophisticated in their `DN` construction patterns might conceivably be impacted. Versions 2.11.15 and 2.12.6 contain a fix. As a workaround, developers should review their CA issuing practices.
```

spans: _(fill in bundle)_

## doc 73 — row_idx 73

```text
In this case, though, running the troubleshooter leads to the installation of LatentBot, a well-documented modular bot used for surveillance, information stealing, and remote access.
```

spans: _(fill in bundle)_

## doc 74 — row_idx 74

```text
Much like the MiniDuke expose in February 2013 , the Dukes again appeared to prioritize continuing operations over staying hidden .
```

spans: _(fill in bundle)_

## doc 75 — row_idx 75

```text
COATHANGER is a remote access tool (RAT) targeting FortiGate networking appliances. First used in 2023 in targeted intrusions against military and government entities in the Netherlands along with other victims, COATHANGER was disclosed in early 2024, with a high confidence assessment linking this malware to a state-sponsored entity in the People's Republic of China. COATHANGER is delivered after gaining access to a FortiGate device, with in-the-wild observations linked to exploitation of CVE-2022-42475. The name COATHANGER is based on a unique string in the malware used to encrypt configuration files on disk: “She took his coat and hung it up”.
```

spans: _(fill in bundle)_

## doc 76 — row_idx 76

```text
In the Linux kernel, the following vulnerability has been resolved:

nvmet: fix freeing unallocated p2pmem

In case p2p device was found but the p2p pool is empty, the nvme target
is still trying to free the sgl from the p2p pool instead of the
regular sgl pool and causing a crash (BUG() is called). Instead, assign
the p2p_dev for the request only if it was allocated from p2p pool.

This is the crash that was caused:

[Sun May 30 19:13:53 2021] ------------[ cut here ]------------
[Sun May 30 19:13:53 2021] kernel BUG at lib/genalloc.c:518!
[Sun May 30 19:13:53 2021] invalid opcode: 0000 [#1] SMP PTI
...
[Sun May 30 19:13:53 2021] kernel BUG at lib/genalloc.c:518!
...
[Sun May 30 19:13:53 2021] RIP: 0010:gen_pool_free_owner+0xa8/0xb0
...
[Sun May 30 19:13:53 2021] Call Trace:
[Sun May 30 19:13:53 2021] ------------[ cut here ]------------
[Sun May 30 19:13:53 2021]  pci_free_p2pmem+0x2b/0x70
[Sun May 30 19:13:53 2021]  pci_p2pmem_free_sgl+0x4f/0x80
[Sun May 30 19:13:53 2021]  nvmet_req_free_sgls+0x1e/0x80 [nvmet]
[Sun May 30 19:13:53 2021] kernel BUG at lib/genalloc.c:518!
[Sun May 30 19:13:53 2021]  nvmet_rdma_release_rsp+0x4e/0x1f0 [nvmet_rdma]
[Sun May 30 19:13:53 2021]  nvmet_rdma_send_done+0x1c/0x60 [nvmet_rdma]
```

spans: _(fill in bundle)_

## doc 77 — row_idx 77

```text
An Improper Check or Handling of Exceptional Conditions vulnerability in packet processing of Juniper Networks Junos OS on QFX10002 allows an unauthenticated, adjacent attacker on the local broadcast domain sending a malformed packet to the device, causing all PFEs other than the inbound PFE to wedge and to eventually restart, resulting in a Denial of Service (DoS) condition. Continued receipt and processing of this packet will create a sustained Denial of Service (DoS) condition. This issue can only be triggered by sending a specific malformed packet to the device. Transit traffic does not trigger this issue. An indication of this issue occurring can be seen through the following log messages: fpc0 expr_hostbound_packet_handler: Receive pe 73? fpc0 Cmerror Op Set: PE Chip: PE0[0]: PGQ:misc_intr: 0x00000020: Enqueue of a packet with out-of-range VOQ in 192K-VOQ mode (URI: /fpc/0/pfe/0/cm/0/PE_Chip/0/PECHIP_CMERROR_PGQ_MISC_INT_EVENTS_ENQ_192K_VIOL) The logs list below can also be observed when this issue occurs fpc0 Error: /fpc/0/pfe/0/cm/0/PE_Chip/0/PECHIP_CMERROR_PGQ_MISC_INT_EVENTS_ENQ_192K_VIOL (0x210107), scope: pfe, category: functional, severity: major, module: PE Chip, type: Description for PECHIP_CMERROR_PGQ_MISC_INT_EVENTS_ENQ_192K_VIOL fpc0 Performing action cmalarm for error /fpc/0/pfe/0/cm/0/PE_Chip/0/PECHIP_CMERROR_PGQ_MISC_INT_EVENTS_ENQ_192K_VIOL (0x210107) in module: PE Chip with scope: pfe category: functional level: major fpc0 Error: /fpc/0/pfe/0/cm/0/PE_Chip/0/PECHIP_CMERROR_CM_INT_REG_DCHK_PIPE (0x21011a), scope: pfe, category: functional, severity: fatal, module: PE Chip, type: Description for PECHIP_CMERROR_CM_INT_REG_DCHK_PIPE fpc0 Performing action cmalarm for error /fpc/0/pfe/0/cm/0/PE_Chip/0/PECHIP_CMERROR_CM_INT_REG_DCHK_PIPE (0x21011a) in module: PE Chip with scope: pfe category: functional level: fatal fpc0 Performing action disable-pfe for error /fpc/0/pfe/0/cm/0/PE_Chip/0/PECHIP_CMERROR_CM_INT_REG_DCHK_PIPE (0x21011a) in module: PE Chip with scope: pfe category: functional level: fatal This issue affects Juniper Networks Junos OS on QFX10002: All versions prior to 19.1R3-S10; 19.4 versions prior to 19.4R3-S11; 20.2 versions prior to 20.2R3-S7; 20.4 versions prior to 20.4R3-S6; 21.1 versions prior to 21.1R3-S4; 21.2 versions prior to 21.2R3-S4; 21.3 versions prior to 21.3R3-S3; 21.4 versions prior to 21.4R3-S2; 22.1 versions prior to 22.1R3-S1; 22.2 versions prior to 22.2R2-S1, 22.2R3; 22.3 versions prior to 22.3R1-S2, 22.3R2.
```

spans: _(fill in bundle)_

## doc 78 — row_idx 78

```text
LibreNMS is an auto-discovering PHP/MySQL/SNMP based network monitoring tool. Versions 25.12.0 and below contain an SQL Injection vulnerability in the ajax_table.php endpoint. The application fails to properly sanitize or parameterize user input when processing IPv6 address searches. Specifically, the address parameter is split into an address and a prefix, and the prefix portion is directly concatenated into the SQL query string without validation. This allows an attacker to inject arbitrary SQL commands, potentially leading to unauthorized data access or database manipulation. This issue has been fixed in version 26.2.0.
```

spans: _(fill in bundle)_

## doc 79 — row_idx 79

```text
Vulnerability Advisory: CVE-2023-45005 is a critical race condition affecting Citrix NetScaler. CrowdStrike confirmed active exploitation by Star Blizzard in the wild. Exploitation delivers DanaBot (SHA1: 8694a04b8d7eaf0d405abd673d69d9878663e9cd) which is dropped to /etc/cron.d/payload.bin. The exploit payload is hosted at hxxp://apiupdate.link/assets/js/payload.js and communicates to 192.187.179.185 for C2.
```

spans: _(fill in bundle)_

## doc 80 — row_idx 80

```text
A Bootkit is a rootkit malware variant which infects the device at start-up and may encrypt disk or steal data , remove the application , open connection for Command and controller .
```

spans: _(fill in bundle)_

## doc 81 — row_idx 81

```text
In this case , like others before , the event of a popular game release became an opportunity to trick unsuspecting users into downloading the RAT . The APT actor , active since 2008 , has been seen targeting organizations in the financial services , telecoms , government , and defense sectors . 3[ . ]doc : d4eb4035e11da04841087a181c48cd85f75c620a84832375925e6b03973d8e48 . The second , CVE-2022 - 41080 , has not been publicly detailed but its CVSS score of 8.8 is the same as CVE-2022 - 41040 used in the ProxyNotShell exploit chain , and it has been marked “ exploitation more likely . ”
```

spans: _(fill in bundle)_

## doc 82 — row_idx 82

```text
In the Linux kernel, the following vulnerability has been resolved:

scsi: ufs: core: mcq: Fix &hwq->cq_lock deadlock issue

When ufshcd_err_handler() is executed, CQ event interrupt can enter waiting
for the same lock. This can happen in ufshcd_handle_mcq_cq_events() and
also in ufs_mtk_mcq_intr(). The following warning message will be generated
when &hwq->cq_lock is used in IRQ context with IRQ enabled. Use
ufshcd_mcq_poll_cqe_lock() with spin_lock_irqsave instead of spin_lock to
resolve the deadlock issue.

[name:lockdep&]WARNING: inconsistent lock state
[name:lockdep&]--------------------------------
[name:lockdep&]inconsistent {IN-HARDIRQ-W} -> {HARDIRQ-ON-W} usage.
[name:lockdep&]kworker/u16:4/260 [HC0[0]:SC0[0]:HE1:SE1] takes:
  ffffff8028444600 (&hwq->cq_lock){?.-.}-{2:2}, at:
ufshcd_mcq_poll_cqe_lock+0x30/0xe0
[name:lockdep&]{IN-HARDIRQ-W} state was registered at:
  lock_acquire+0x17c/0x33c
  _raw_spin_lock+0x5c/0x7c
  ufshcd_mcq_poll_cqe_lock+0x30/0xe0
  ufs_mtk_mcq_intr+0x60/0x1bc [ufs_mediatek_mod]
  __handle_irq_event_percpu+0x140/0x3ec
  handle_irq_event+0x50/0xd8
  handle_fasteoi_irq+0x148/0x2b0
  generic_handle_domain_irq+0x4c/0x6c
  gic_handle_irq+0x58/0x134
  call_on_irq_stack+0x40/0x74
  do_interrupt_handler+0x84/0xe4
  el1_interrupt+0x3c/0x78
<snip>

Possible unsafe locking scenario:
       CPU0
       ----
  lock(&hwq->cq_lock);
  <Interrupt>
    lock(&hwq->cq_lock);
  *** DEADLOCK ***
2 locks held by kworker/u16:4/260:

[name:lockdep&]
 stack backtrace:
CPU: 7 PID: 260 Comm: kworker/u16:4 Tainted: G S      W  OE
6.1.17-mainline-android14-2-g277223301adb #1
Workqueue: ufs_eh_wq_0 ufshcd_err_handler

 Call trace:
  dump_backtrace+0x10c/0x160
  show_stack+0x20/0x30
  dump_stack_lvl+0x98/0xd8
  dump_stack+0x20/0x60
  print_usage_bug+0x584/0x76c
  mark_lock_irq+0x488/0x510
  mark_lock+0x1ec/0x25c
  __lock_acquire+0x4d8/0xffc
  lock_acquire+0x17c/0x33c
  _raw_spin_lock+0x5c/0x7c
  ufshcd_mcq_poll_cqe_lock+0x30/0xe0
  ufshcd_poll+0x68/0x1b0
  ufshcd_transfer_req_compl+0x9c/0xc8
  ufshcd_err_handler+0x3bc/0xea0
  process_one_work+0x2f4/0x7e8
  worker_thread+0x234/0x450
  kthread+0x110/0x134
  ret_from_fork+0x10/0x20
```

spans: _(fill in bundle)_

## doc 83 — row_idx 83

```text
A vulnerability named 'Non-Responsive Delegation Attack' (NRDelegation Attack) has been discovered in various DNS resolving software. The NRDelegation Attack works by having a malicious delegation with a considerable number of non responsive nameservers. The attack starts by querying a resolver for a record that relies on those unresponsive nameservers. The attack can cause a resolver to spend a lot of time/resources resolving records under a malicious delegation point where a considerable number of unresponsive NS records reside. It can trigger high CPU usage in some resolver implementations that continually look in the cache for resolved NS records in that delegation. This can lead to degraded performance and eventually denial of service in orchestrated attacks. Unbound does not suffer from high CPU usage, but resources are still needed for resolving the malicious delegation. Unbound will keep trying to resolve the record until hard limits are reached. Based on the nature of the attack and the replies, different limits could be reached. From version 1.16.3 on, Unbound introduces fixes for better performance when under load, by cutting opportunistic queries for nameserver discovery and DNSKEY prefetching and limiting the number of times a delegation point can issue a cache lookup for missing records.
```

spans: _(fill in bundle)_

## doc 84 — row_idx 84

```text
Pacu is an open-source AWS exploitation framework. The tool is written in Python and publicly available on GitHub.
```

spans: _(fill in bundle)_

## doc 85 — row_idx 85

```text
The first DNS query by Glimpse requests the mode to be used in future communications with the controller (i.e., ping mode or text mode ) .
```

spans: _(fill in bundle)_

## doc 86 — row_idx 86

```text
APT15 was targeting information related to UK government departments and military technology .
```

spans: _(fill in bundle)_

## doc 87 — row_idx 87

```text
Our friends over at Bellingcat, which conducts open source investigations and writes extensively on Russia-related issues, recently shared a new tranche of spear-phishing emails they had received.
```

spans: _(fill in bundle)_

## doc 88 — row_idx 88

```text
Starloader is a loader component that has been observed loading Felismus and associated tools.
```

spans: _(fill in bundle)_

## doc 89 — row_idx 89

```text
Malware Analysis Report: TrickBot (SHA1: 5ba325473f41beb4cb02c4a65e20e8074e1fb9d8). Upon execution on Fortinet FortiGate, the sample creates C:\Windows\Tasks\backdoor.elf and injects into legitimate processes. Network analysis shows beaconing to 192.131.150.214 every 60 seconds and DNS queries to updatestorage.site. The second stage was fetched from hxxp://storageedge.io/wp-content/uploads/doc.php and written to C:\Users\Public\Documents\chrome_helper.exe. The payload uses PsExec-style techniques for defense evasion. A secondary hash (SHA256: 559214a0883554e8ce7423b32eb5d7c90bcfcb3301295a52974f872d4790b29c) was extracted from the unpacked payload.
```

spans: _(fill in bundle)_

## doc 90 — row_idx 90

```text
The main payload is usually Imminent Monitor RAT; however , at the beginning of 2018 , we also observed the use of LuminosityLink RAT , NetWire RAT , and NjRAT .
```

spans: _(fill in bundle)_

## doc 91 — row_idx 91

```text
] ir . In recent APT incidents , Dark Hydruns tend to adopt Office VBA macro instead of Office 0day vulnerability in the consideration of cost reduction . ScarCruft tools : 22aaf617a86e026424edb7c868742495 AV Remover .
```

spans: _(fill in bundle)_

## doc 92 — row_idx 92

```text
In previous instances, Cyble Research and Intelligence Labs CRIL has exposed numerous phishing websites that have been used to steal sensitive data by utilizing a range of malware types, such as stealers, RATs, and bots.
```

spans: _(fill in bundle)_

## doc 93 — row_idx 93

```text
Adversaries may use a Login Hook to establish persistence executed upon user logon. A login hook is a plist file that points to a specific script to execute with root privileges upon user logon. The plist file is located in the /Library/Preferences/com.apple.loginwindow.plist file and can be modified using the defaults command-line utility. This behavior is the same for logout hooks where a script can be executed upon user logout. All hooks require administrator permissions to modify or create hooks. 

Adversaries can add or insert a path to a malicious script in the com.apple.loginwindow.plist file, using the LoginHook or LogoutHook key-value pair. The malicious script is executed upon the next user login. If a login hook already exists, adversaries can add additional commands to an existing login hook. There can be only one login and logout hook on a system at a time.

**Note:** Login hooks were deprecated in 10.11 version of macOS in favor of Launch Daemon and Launch Agent
```

spans: _(fill in bundle)_

## doc 94 — row_idx 94

```text
This background image likely contains a fake “ software update ” screen . Alternatively , OurMine might have used social engineering to trick WikiLeaks 's DNS provider into handing over the credentials , or simple requested that a password reset link be sent to a compromised email address . The group has maintained a low profile until now and its targets have been mainly organizations and individuals that would be of interest to a nation state 's intelligence services .
```

spans: _(fill in bundle)_

## doc 95 — row_idx 95

```text
IOC Bulletin - Play Campaign:
Network Indicators:
- 172.189.37.110
- 126.47.86.29
- 192.220.24.213
- edge-api.dev
- login-data.live
URLs:
- https://cloud-cdn.org/secure/token
- http://cachelogin.com/download/update.exe
Email Senders:
- helpdesk@secure-verify.net
- finance@auth-check.org
File Indicators:
- SHA1: 58b25e5ee5b28145180a15449580a8bc454ce187
- SHA1: 69d7c215099b56d8069ae1ed37fbcc426660d03b
- Drop path: C:\Program Files\Common Files\dropper.ps1
```

spans: _(fill in bundle)_

## doc 96 — row_idx 96

```text
In the Linux kernel, the following vulnerability has been resolved:

vduse: fix NULL pointer dereference

vduse_vdpa_set_vq_affinity callback can be called
with NULL value as cpu_mask when deleting the vduse
device.

This patch resets virtqueue's IRQ affinity mask value
to set all CPUs instead of dereferencing NULL cpu_mask.

[ 4760.952149] BUG: kernel NULL pointer dereference, address: 0000000000000000
[ 4760.959110] #PF: supervisor read access in kernel mode
[ 4760.964247] #PF: error_code(0x0000) - not-present page
[ 4760.969385] PGD 0 P4D 0
[ 4760.971927] Oops: 0000 [#1] PREEMPT SMP PTI
[ 4760.976112] CPU: 13 PID: 2346 Comm: vdpa Not tainted 6.4.0-rc6+ #4
[ 4760.982291] Hardware name: Dell Inc. PowerEdge R640/0W23H8, BIOS 2.8.1 06/26/2020
[ 4760.989769] RIP: 0010:memcpy_orig+0xc5/0x130
[ 4760.994049] Code: 16 f8 4c 89 07 4c 89 4f 08 4c 89 54 17 f0 4c 89 5c 17 f8 c3 cc cc cc cc 66 66 2e 0f 1f 84 00 00 00 00 00 66 90 83 fa 08 72 1b <4c> 8b 06 4c 8b 4c 16 f8 4c 89 07 4c 89 4c 17 f8 c3 cc cc cc cc 66
[ 4761.012793] RSP: 0018:ffffb1d565abb830 EFLAGS: 00010246
[ 4761.018020] RAX: ffff9f4bf6b27898 RBX: ffff9f4be23969c0 RCX: ffff9f4bcadf6400
[ 4761.025152] RDX: 0000000000000008 RSI: 0000000000000000 RDI: ffff9f4bf6b27898
[ 4761.032286] RBP: 0000000000000000 R08: 0000000000000008 R09: 0000000000000000
[ 4761.039416] R10: 0000000000000000 R11: 0000000000000600 R12: 0000000000000000
[ 4761.046549] R13: 0000000000000000 R14: 0000000000000080 R15: ffffb1d565abbb10
[ 4761.053680] FS:  00007f64c2ec2740(0000) GS:ffff9f635f980000(0000) knlGS:0000000000000000
[ 4761.061765] CS:  0010 DS: 0000 ES: 0000 CR0: 0000000080050033
[ 4761.067513] CR2: 0000000000000000 CR3: 0000001875270006 CR4: 00000000007706e0
[ 4761.074645] DR0: 0000000000000000 DR1: 0000000000000000 DR2: 0000000000000000
[ 4761.081775] DR3: 0000000000000000 DR6: 00000000fffe0ff0 DR7: 0000000000000400
[ 4761.088909] PKRU: 55555554
[ 4761.091620] Call Trace:
[ 4761.094074]  <TASK>
[ 4761.096180]  ? __die+0x1f/0x70
[ 4761.099238]  ? page_fault_oops+0x171/0x4f0
[ 4761.103340]  ? exc_page_fault+0x7b/0x180
[ 4761.107265]  ? asm_exc_page_fault+0x22/0x30
[ 4761.111460]  ? memcpy_orig+0xc5/0x130
[ 4761.115126]  vduse_vdpa_set_vq_affinity+0x3e/0x50 [vduse]
[ 4761.120533]  virtnet_clean_affinity.part.0+0x3d/0x90 [virtio_net]
[ 4761.126635]  remove_vq_common+0x1a4/0x250 [virtio_net]
[ 4761.131781]  virtnet_remove+0x5d/0x70 [virtio_net]
[ 4761.136580]  virtio_dev_remove+0x3a/0x90
[ 4761.140509]  device_release_driver_internal+0x19b/0x200
[ 4761.145742]  bus_remove_device+0xc2/0x130
[ 4761.149755]  device_del+0x158/0x3e0
[ 4761.153245]  ? kernfs_find_ns+0x35/0xc0
[ 4761.157086]  device_unregister+0x13/0x60
[ 4761.161010]  unregister_virtio_device+0x11/0x20
[ 4761.165543]  device_release_driver_internal+0x19b/0x200
[ 4761.170770]  bus_remove_device+0xc2/0x130
[ 4761.174782]  device_del+0x158/0x3e0
[ 4761.178276]  ? __pfx_vdpa_name_match+0x10/0x10 [vdpa]
[ 4761.183336]  device_unregister+0x13/0x60
[ 4761.187260]  vdpa_nl_cmd_dev_del_set_doit+0x63/0xe0 [vdpa]
```

spans: _(fill in bundle)_

## doc 97 — row_idx 97

```text
Typhon is an info stealer first that was reported in mid-2022 for the first time.
```

spans: _(fill in bundle)_

## doc 98 — row_idx 98

```text
A backdoor also known as: Trojan.Win32.VBKrypt!O Worm.Rebhip.B3 Troj.W32.Scar!c Trojan/Injector.eyu Trojan.Win32.Scar.odxb Trojan.Win32.VBKrypt.ecjqdh Trojan.Win32.A.VBKrypt.200710 TrojWare.Win32.VBKrypt.cjb Trojan.Inject.27856 Trojan.VBKrypt.Win32.39868 BehavesLike.Win32.PWSSpyeye.cc W32/Trojan.FNVH-2986 Trojan/VBKrypt.bgwm Trojan/Win32.VBKrypt Trojan.ManBat.1 Trojan.Win32.Scar.odxb Trojan/Win32.VBKrypt.C66955 PWS-Spyeye.el SScope.Malware-Cryptor.VBCR.1841 Win32.Trojan.Scar.Tccd Trojan.VBKrypt!joEshOiwspo Win32/Trojan.00c
```

spans: _(fill in bundle)_

## doc 99 — row_idx 99

```text
The investigation found a supply chain-focused attack at M.E.Doc software that delivered a destructive payload disguised as ransomware.
```

spans: _(fill in bundle)_

