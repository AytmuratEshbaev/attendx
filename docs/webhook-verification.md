# AttendX Webhook Signature Verification

## How it works

Every webhook delivery includes an HMAC-SHA256 signature in the `X-AttendX-Signature` header.
The signature is computed over the raw JSON payload body using your webhook's secret key.

## Headers included in every delivery

| Header | Description |
|--------|-------------|
| `X-AttendX-Signature` | `sha256=<hex-digest>` HMAC-SHA256 signature |
| `X-AttendX-Event` | Event type, e.g. `attendance.entry` |
| `X-AttendX-Delivery` | Unique delivery ID (UUID) |
| `X-AttendX-Timestamp` | Unix timestamp of delivery |
| `Content-Type` | `application/json; charset=utf-8` |
| `User-Agent` | `AttendX-Webhook/1.0` |

## Payload format

```json
{
  "event": "attendance.entry",
  "delivery_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-02-17T10:30:00.000000+00:00",
  "data": {
    "student_id": "...",
    "student_name": "...",
    "event_time": "..."
  }
}
```

## Verification examples

### Python

```python
import hmac
import hashlib

def verify_webhook(secret: str, payload_body: bytes, signature_header: str) -> bool:
    expected = hmac.new(
        secret.encode("utf-8"),
        payload_body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature_header)

# Usage in Flask/FastAPI:
# raw_body = await request.body()
# signature = request.headers["X-AttendX-Signature"]
# is_valid = verify_webhook("your-secret", raw_body, signature)
```

### Node.js

```javascript
const crypto = require('crypto');

function verifyWebhook(secret, payloadBody, signatureHeader) {
    const expected = crypto
        .createHmac('sha256', secret)
        .update(payloadBody)
        .digest('hex');
    const expectedSig = `sha256=${expected}`;
    return crypto.timingSafeEqual(
        Buffer.from(expectedSig),
        Buffer.from(signatureHeader)
    );
}

// Usage in Express:
// app.post('/webhook', express.raw({type: 'application/json'}), (req, res) => {
//     const sig = req.headers['x-attendx-signature'];
//     if (!verifyWebhook('your-secret', req.body, sig)) {
//         return res.status(401).send('Invalid signature');
//     }
//     const event = JSON.parse(req.body);
//     // Process event...
//     res.status(200).send('OK');
// });
```

### PHP

```php
function verifyWebhook(string $secret, string $payloadBody, string $signatureHeader): bool {
    $expected = 'sha256=' . hash_hmac('sha256', $payloadBody, $secret);
    return hash_equals($expected, $signatureHeader);
}

// Usage:
// $payload = file_get_contents('php://input');
// $signature = $_SERVER['HTTP_X_ATTENDX_SIGNATURE'];
// if (!verifyWebhook('your-secret', $payload, $signature)) {
//     http_response_code(401);
//     exit('Invalid signature');
// }
```

### Go

```go
package main

import (
    "crypto/hmac"
    "crypto/sha256"
    "encoding/hex"
    "fmt"
)

func verifyWebhook(secret, payloadBody, signatureHeader string) bool {
    mac := hmac.New(sha256.New, []byte(secret))
    mac.Write([]byte(payloadBody))
    expected := fmt.Sprintf("sha256=%s", hex.EncodeToString(mac.Sum(nil)))
    return hmac.Equal([]byte(expected), []byte(signatureHeader))
}
```

## Available event types

| Event | Description |
|-------|-------------|
| `attendance.entry` | Student entered (face recognized at entry terminal) |
| `attendance.exit` | Student exited (face recognized at exit terminal) |
| `student.created` | New student record created |
| `student.updated` | Student information updated |
| `student.deleted` | Student deactivated/deleted |
| `device.online` | Hikvision terminal came online |
| `device.offline` | Hikvision terminal went offline |
| `face.registered` | Student face registered on terminals |
| `webhook.test` | Test ping from admin dashboard |

## Security recommendations

1. **Always verify signatures** before processing webhook payloads
2. **Use HTTPS** endpoints to receive webhooks
3. **Respond quickly** (within 30 seconds) to avoid timeouts
4. **Return 2xx** status codes to acknowledge receipt
5. **Process asynchronously** — queue the event and return 200 immediately
6. **Check the timestamp** to prevent replay attacks (reject events older than 5 minutes)
