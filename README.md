# DANSHI PANEL

نسخه‌ی اولیه پنل مدیریت VLESS.

## نصب روی Ubuntu VPS

```bash
sudo apt update
sudo apt install -y python3 python3-venv
git clone YOUR_PROJECT_URL danshi-panel
cd danshi-panel
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000
```

سپس:
`http://SERVER_IP:8000`

## اطلاعات ورود اولیه
- username: `admin`
- password: `change-me-now`

حتماً قبل از استفاده‌ی عمومی، این مقادیر را در `app.py` تغییر بده.

## نکته
این نسخه فقط پنل مدیریتی و تولید URI است و خودش Xray را نصب/تغییر نمی‌دهد. در مرحله بعد می‌توان API امن برای مدیریت Xray، TLS، دامنه، محدودیت حجم و انقضا اضافه کرد.
