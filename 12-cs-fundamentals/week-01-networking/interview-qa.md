# Week 1 - Networking: Interview Q&A

Practice: answer out loud in 30-60 seconds first, then compare.

---

**1. Explain the OSI and TCP/IP models and where common devices and protocols sit.**
OSI has seven layers; TCP/IP collapses them to four: link, internet, transport, application. Ethernet/Wi-Fi and MAC addresses are L2, IP and routers are L3, TCP/UDP are L4, and HTTP, DNS, and TLS (loosely) are above that. Each layer encapsulates the one above: HTTP bytes get a TCP header, then an IP header, then an Ethernet frame. MAC addresses change every hop; IP addresses stay end-to-end (barring NAT). A switch forwards by MAC, a router by IP, and load balancers are L4 (IP:port, e.g. NLB) or L7 (host/path/headers, e.g. ALB).

**2. How many usable hosts are in a /27, and which /20 contains 172.16.37.200?**
A /27 has 5 host bits, so 32 addresses and 30 usable on a classic LAN (cloud providers reserve more; AWS reserves 5, so 27; check current docs). For a /20 the mask is 255.255.240.0, so the third-octet block size is 16. 37 falls in the block starting at 32, so the network is 172.16.32.0/20, range 172.16.32.0 to 172.16.47.255, 4096 addresses.

**3. What is CIDR, longest-prefix match, and why do overlapping CIDRs hurt?**
CIDR writes a network as address/prefix-length, replacing rigid classes and allowing aggregation and arbitrary splits. Routers choose the matching route with the longest prefix, so 10.1.0.0/16 beats 10.0.0.0/8 for 10.1.2.3. If two networks that must connect (VPC peering, VPN, customer data center) overlap, a router cannot tell which side an address belongs to, so routing is ambiguous or impossible. In customer deployments I ask for their ranges before choosing mine.

**4. Walk through the TCP three-way handshake and what it establishes.**
The client sends SYN with its initial sequence number, the server replies SYN-ACK with its own number and acknowledges the client's, and the client sends ACK. After that both sides are ESTABLISHED, both directions are confirmed working, and sequence numbers are synchronized. It costs one RTT before data flows. SYN floods exploit half-open state and are mitigated with SYN cookies; the server also has a separate accept queue sized by the listen backlog, which can overflow if the app accepts slowly.

**5. Why does TIME_WAIT exist, and how does it differ from CLOSE_WAIT?**
TIME_WAIT is held by the side that closes first for about 2 MSL (around 60 s on Linux; check current docs) so delayed duplicate segments expire and the final ACK can be retransmitted. Many of them on a client or proxy can exhaust ephemeral ports; fix with connection pooling/keep-alive, a wider port range, or more source IPs, not by disabling the safety mechanism. CLOSE_WAIT means the peer closed and your application has not called close(); a pile of them is an application socket leak.

**6. Flow control versus congestion control?**
Flow control protects the receiver: the receiver advertises a window (rwnd) in ACKs so the sender does not overrun its buffer. Congestion control protects the network: the sender maintains a congestion window (cwnd) inferred from loss or delay. Bytes in flight are limited to the minimum of the two. Throughput is capped at window/RTT, so on high bandwidth-delay-product links you need window scaling and large windows to fill the pipe.

**7. Explain slow start and congestion avoidance.**
A new connection starts with a small congestion window (about 10 segments typically; check current docs) and doubles it each RTT during slow start until it hits ssthresh or detects loss. After that, congestion avoidance grows it linearly, about one segment per RTT. On loss, the sender cuts ssthresh and cwnd (halving on triple duplicate ACKs, more harshly on timeout). The implication is that short transfers never reach full speed, so reducing round trips (keep-alive, HTTP/2, TLS 1.3, CDNs) matters more than bandwidth. CUBIC is the common Linux default and BBR is a model-based alternative.

**8. How does TCP detect and recover from loss?**
Receivers send cumulative ACKs, optionally with SACK to describe later received ranges. The sender retransmits when a retransmission timer (RTO, with exponential backoff) fires or after three duplicate ACKs (fast retransmit), which avoids waiting for the timeout. Retransmits shrink the congestion window, so loss hurts throughput twice: the delay and the slowdown. TCP guarantees ordered delivery to the peer's kernel, not that the peer application processed the data.

**9. When would you choose UDP over TCP?**
When latency matters more than perfect delivery, or when the application wants its own reliability and framing: real-time voice and video, games, DNS queries, DHCP, and QUIC (the base of HTTP/3). UDP has no handshake, no ordering, no congestion control, and preserves message boundaries, so the app must handle loss, pacing, and fairness. Keep datagrams under about 1200 bytes to avoid fragmentation.

**10. Describe DNS resolution from a browser to an answer, and recursive versus authoritative servers.**
The browser and OS check their caches and /etc/hosts, then the stub resolver asks a recursive resolver. On a cache miss, the recursive resolver asks a root server for the TLD servers, a TLD server for the domain's authoritative name servers, and then the authoritative server, which holds the actual records. The recursive resolver caches the answer for its TTL and returns it. Recursive resolvers do the legwork and cache; authoritative servers answer only for their zones and do not recurse.

**11. A DNS record was changed an hour ago but some users still hit the old IP. Why, and how do you prevent it?**
Resolvers, OSes, browsers, and long-lived processes (JVM, Python services holding connections) cache by TTL, and some ignore low TTLs. Negative answers (NXDOMAIN) are cached too. The prevention is to lower the TTL well before the change (for example 300 s a day ahead), make the change, and raise the TTL afterward; also recycle connections or re-resolve in clients. To diagnose, query specific resolvers with `dig @resolver name` and compare the remaining TTL.

**12. What are the key DNS record types and a CNAME restriction?**
A and AAAA map names to IPv4 and IPv6, CNAME aliases one name to another, NS delegates zones, MX routes mail, TXT carries SPF/DKIM and verification strings, SRV gives host and port, PTR does reverse lookups, SOA holds zone metadata and the negative-cache TTL, and CAA restricts which CAs may issue certificates. A CNAME cannot coexist with other records at the same name, so it cannot sit at the zone apex (which needs SOA and NS); providers offer ALIAS/ANAME-style flattening instead.

**13. What is head-of-line blocking, and how do HTTP/1.1, HTTP/2, and HTTP/3 differ?**
HTTP/1.1 handles one request at a time per connection, so a slow response blocks later ones (browsers open about six connections to cope). HTTP/2 multiplexes many streams over one TCP connection with binary framing and HPACK header compression, removing HTTP-level blocking, but one lost packet still stalls every stream because TCP delivers bytes in order. HTTP/3 runs over QUIC on UDP with independent streams, built-in TLS 1.3, faster setup, and connection migration, so loss affects only the stream involved. UDP can be blocked by corporate firewalls, so clients must fall back to HTTP/2.

**14. Walk through a TLS 1.3 handshake and what a certificate proves.**
The client sends ClientHello with supported ciphers, a key share, SNI, and ALPN. The server replies with its key share, then (encrypted) its certificate chain, a signature proving it holds the private key, and Finished; the client finishes, and application data flows after one round trip. The ephemeral Diffie-Hellman exchange yields forward secrecy, and symmetric keys encrypt the bulk data. A certificate binds a public key to names (SAN) and is signed by a CA; the client validates the chain up to a trusted root, checks dates and hostname, and the signature proves the server controls the key. TLS 1.2 needed two round trips.

**15. What is SNI, and what is mTLS?**
SNI is the hostname the client sends in ClientHello so one IP and port can serve many certificates; without it (for example curling a raw IP) the server returns a default certificate and you see a name mismatch, and `curl --resolve` lets you keep SNI while overriding DNS. In mTLS the server also requests and verifies a client certificate, giving strong mutual identity for service-to-service calls, service meshes, and B2B APIs. Typical failures are missing or untrusted client certs, which show up as handshake alerts like "bad certificate".

**16. How do you debug an SSL certificate error at a customer site?**
Run `openssl s_client -connect host:443 -servername host -showcerts` and read the verify code, the chain, issuer, SAN, and dates. Expired means renewal or a wrong client clock; hostname mismatch means wrong cert, missing SNI, or connecting by IP; "unable to get local issuer" means the server omitted an intermediate or the client lacks the corporate root CA, often from a TLS-inspecting proxy whose CA is not trusted; protocol or cipher failures mean version mismatch. Compare what the customer's environment sees against a clean network, since a different issuer exposes an inspecting proxy. Never recommend `-k` or `verify=False` as a fix.

**17. Explain 401 vs 403, 502 vs 504, and idempotency of HTTP methods.**
401 means not authenticated (missing or invalid credentials); 403 means authenticated but not allowed. 502 means the gateway got an invalid response or the upstream connection failed or reset; 504 means the upstream did not respond within the gateway timeout. GET, PUT, DELETE, HEAD, and OPTIONS are idempotent (repeats have the same effect), POST is not (use an Idempotency-Key for safe retries), and PATCH is not guaranteed. Idempotency decides which requests clients may safely retry.

**18. How do Cache-Control and ETag work together?**
`Cache-Control: max-age=N` makes a response fresh for N seconds with no network use; `s-maxage` targets shared caches, `private` restricts to the browser, `no-store` forbids storage, and `no-cache` allows storing but requires revalidation. After expiry the client sends `If-None-Match` with the stored ETag, and an unchanged resource gets a body-less 304, saving bandwidth. `Vary` lists request headers that change the response so caches key correctly; a wrong Vary can serve one user's response to another. ETags with If-Match also provide optimistic concurrency control on writes.

**19. What is CORS, what triggers a preflight, and why does curl work while the browser fails?**
The same-origin policy blocks a page from reading cross-origin responses; CORS lets a server opt in with Access-Control-Allow-Origin and related headers. It is enforced only by browsers, so curl is unaffected. Requests with methods other than simple ones, JSON content type, Authorization, or custom headers trigger an OPTIONS preflight asking permission; the server must answer with the allowed origin, methods, and headers (Access-Control-Max-Age caches it). With cookies you need Allow-Credentials and an explicit origin, not `*`. In FastAPI, use CORSMiddleware with explicit origins; a preflight that returns 401 or 404 is a common cause of failure.

**20. Sessions versus JWTs, and how do cookie attributes help?**
Server sessions store state (in Redis or a database) behind an opaque cookie, which makes revocation easy but needs a shared store. JWTs are signed tokens carrying claims that any service can verify with the key, so they scale statelessly, but they cannot be revoked before expiry without a denylist, so use short lifetimes plus refresh tokens, and always validate signature, exp, iss, aud, and a pinned algorithm; the payload is encoded, not encrypted. For cookies, HttpOnly blocks script access (limits XSS theft), Secure forces HTTPS, and SameSite (Lax or Strict) reduces CSRF. Tokens in localStorage are readable by XSS; cookies need CSRF protection; know and state the trade-off.
