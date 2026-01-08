# VisionCraftAI API クイックスタート

## 5分でAPI連携を始める

### ステップ1: APIキーを取得

```bash
curl -X POST https://api.visioncraftai.com/api/v1/auth/keys \
  -H "Content-Type: application/json" \
  -d '{"tier": "free", "name": "QuickStart Key"}'
```

### ステップ2: 画像を生成

```bash
curl -X POST https://api.visioncraftai.com/api/v1/generate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{"prompt": "A serene Japanese garden with cherry blossoms"}'
```

### ステップ3: 結果を確認

レスポンスの`image_base64`をデコードして画像ファイルとして保存。

---

## 言語別サンプルコード

### Python

```python
import requests
import base64

API_KEY = "vca_xxxxxxxx.xxxxxxxx"
BASE_URL = "https://api.visioncraftai.com"

def generate_image(prompt: str, width: int = 1024, height: int = 1024):
    """画像を生成してファイルに保存"""
    response = requests.post(
        f"{BASE_URL}/api/v1/generate",
        headers={
            "Content-Type": "application/json",
            "X-API-Key": API_KEY
        },
        json={
            "prompt": prompt,
            "width": width,
            "height": height
        }
    )
    response.raise_for_status()

    data = response.json()
    image_bytes = base64.b64decode(data["image_base64"])

    filename = f"generated_{data['id']}.png"
    with open(filename, "wb") as f:
        f.write(image_bytes)

    print(f"画像を保存しました: {filename}")
    return filename

# 使用例
generate_image("A futuristic city at sunset")
```

### JavaScript (Node.js)

```javascript
const axios = require('axios');
const fs = require('fs');

const API_KEY = 'vca_xxxxxxxx.xxxxxxxx';
const BASE_URL = 'https://api.visioncraftai.com';

async function generateImage(prompt, width = 1024, height = 1024) {
    const response = await axios.post(
        `${BASE_URL}/api/v1/generate`,
        { prompt, width, height },
        {
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': API_KEY
            }
        }
    );

    const imageBuffer = Buffer.from(response.data.image_base64, 'base64');
    const filename = `generated_${response.data.id}.png`;

    fs.writeFileSync(filename, imageBuffer);
    console.log(`画像を保存しました: ${filename}`);

    return filename;
}

// 使用例
generateImage('A futuristic city at sunset');
```

### PHP

```php
<?php
$apiKey = 'vca_xxxxxxxx.xxxxxxxx';
$baseUrl = 'https://api.visioncraftai.com';

function generateImage($prompt, $width = 1024, $height = 1024) {
    global $apiKey, $baseUrl;

    $ch = curl_init("$baseUrl/api/v1/generate");
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'Content-Type: application/json',
        "X-API-Key: $apiKey"
    ]);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode([
        'prompt' => $prompt,
        'width' => $width,
        'height' => $height
    ]));

    $response = curl_exec($ch);
    curl_close($ch);

    $data = json_decode($response, true);
    $imageData = base64_decode($data['image_base64']);

    $filename = "generated_{$data['id']}.png";
    file_put_contents($filename, $imageData);

    echo "画像を保存しました: $filename\n";
    return $filename;
}

// 使用例
generateImage('A futuristic city at sunset');
```

### Ruby

```ruby
require 'net/http'
require 'json'
require 'base64'

API_KEY = 'vca_xxxxxxxx.xxxxxxxx'
BASE_URL = 'https://api.visioncraftai.com'

def generate_image(prompt, width: 1024, height: 1024)
  uri = URI("#{BASE_URL}/api/v1/generate")
  http = Net::HTTP.new(uri.host, uri.port)
  http.use_ssl = true

  request = Net::HTTP::Post.new(uri.path)
  request['Content-Type'] = 'application/json'
  request['X-API-Key'] = API_KEY
  request.body = { prompt: prompt, width: width, height: height }.to_json

  response = http.request(request)
  data = JSON.parse(response.body)

  image_data = Base64.decode64(data['image_base64'])
  filename = "generated_#{data['id']}.png"

  File.open(filename, 'wb') { |f| f.write(image_data) }
  puts "画像を保存しました: #{filename}"

  filename
end

# 使用例
generate_image('A futuristic city at sunset')
```

### Go

```go
package main

import (
    "bytes"
    "encoding/base64"
    "encoding/json"
    "fmt"
    "io/ioutil"
    "net/http"
)

const (
    apiKey  = "vca_xxxxxxxx.xxxxxxxx"
    baseURL = "https://api.visioncraftai.com"
)

type GenerateRequest struct {
    Prompt string `json:"prompt"`
    Width  int    `json:"width"`
    Height int    `json:"height"`
}

type GenerateResponse struct {
    ID          string `json:"id"`
    ImageBase64 string `json:"image_base64"`
}

func generateImage(prompt string, width, height int) (string, error) {
    reqBody, _ := json.Marshal(GenerateRequest{
        Prompt: prompt,
        Width:  width,
        Height: height,
    })

    req, _ := http.NewRequest("POST", baseURL+"/api/v1/generate", bytes.NewBuffer(reqBody))
    req.Header.Set("Content-Type", "application/json")
    req.Header.Set("X-API-Key", apiKey)

    client := &http.Client{}
    resp, err := client.Do(req)
    if err != nil {
        return "", err
    }
    defer resp.Body.Close()

    body, _ := ioutil.ReadAll(resp.Body)
    var data GenerateResponse
    json.Unmarshal(body, &data)

    imageData, _ := base64.StdEncoding.DecodeString(data.ImageBase64)
    filename := fmt.Sprintf("generated_%s.png", data.ID)

    ioutil.WriteFile(filename, imageData, 0644)
    fmt.Printf("画像を保存しました: %s\n", filename)

    return filename, nil
}

func main() {
    generateImage("A futuristic city at sunset", 1024, 1024)
}
```

---

## バッチ処理

複数の画像を一度に生成:

```bash
curl -X POST https://api.visioncraftai.com/api/v1/batch/generate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "prompts": [
      "A sunrise over mountains",
      "A sunset over the ocean",
      "A starry night sky"
    ],
    "width": 1024,
    "height": 1024
  }'
```

---

## プロンプト検証

画像生成前にプロンプトを検証:

```bash
curl -X POST https://api.visioncraftai.com/api/v1/prompt/validate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "A beautiful landscape"}'
```

レスポンス:
```json
{
  "is_valid": true,
  "issues": [],
  "suggestions": ["Consider adding style keywords for better results"]
}
```

---

## プロンプト拡張

AIがプロンプトを自動拡張:

```bash
curl -X POST https://api.visioncraftai.com/api/v1/prompt/enhance \
  -H "Content-Type: application/json" \
  -d '{"prompt": "cat"}'
```

レスポンス:
```json
{
  "original": "cat",
  "enhanced": "A cute fluffy cat with bright eyes, soft fur, photorealistic, highly detailed, professional photography, soft natural lighting"
}
```

---

## クォータ確認

残りの生成枠を確認:

```bash
curl https://api.visioncraftai.com/api/v1/auth/quota \
  -H "X-API-Key: YOUR_API_KEY"
```

レスポンス:
```json
{
  "tier": "basic",
  "monthly": {
    "limit": 100,
    "used": 45,
    "remaining": 55
  },
  "daily": {
    "limit": 20,
    "used": 8,
    "remaining": 12
  }
}
```

---

## エラー処理のベストプラクティス

```python
import requests
from requests.exceptions import HTTPError
import time

def generate_with_retry(prompt, max_retries=3):
    """リトライ付き画像生成"""
    for attempt in range(max_retries):
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/generate",
                headers={"X-API-Key": API_KEY},
                json={"prompt": prompt},
                timeout=60
            )
            response.raise_for_status()
            return response.json()

        except HTTPError as e:
            if e.response.status_code == 429:
                # レート制限: 待機してリトライ
                retry_after = int(e.response.headers.get("Retry-After", 60))
                print(f"レート制限。{retry_after}秒待機...")
                time.sleep(retry_after)

            elif e.response.status_code >= 500:
                # サーバーエラー: 待機してリトライ
                wait_time = 2 ** attempt
                print(f"サーバーエラー。{wait_time}秒待機...")
                time.sleep(wait_time)

            else:
                # その他のエラー: 即座に失敗
                raise

    raise Exception("最大リトライ回数を超えました")
```

---

## 次のステップ

1. [完全なAPIドキュメント](/docs) を参照
2. [料金プラン](/#pricing) を確認
3. [お問い合わせ](/contact) でEnterprise相談

---

## サポート

- ドキュメント: https://api.visioncraftai.com/docs
- Email: support@visioncraftai.example.com
- GitHub: https://github.com/VisionCraftAI
