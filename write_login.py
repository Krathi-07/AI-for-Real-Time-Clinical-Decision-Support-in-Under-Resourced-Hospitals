from pathlib import Path

html = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Login | AI Clinical Decision Support</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: "DM Sans", sans-serif;
  background: #0a0d14;
  color: #e2e8f0;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}
.login-wrap {
  width: 100%;
  max-width: 420px;
  padding: 24px;
}
.login-card {
  background: #111827;
  border: 1px solid #1f2937;
  border-radius: 16px;
  padding: 40px;
}
.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 32px;
  justify-content: center;
}
.dot {
  width: 10px; height: 10px;
  border-radius: 50%;
  background: #06b6d4;
  animation: pulse 2s infinite;
}
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }
.logo-text { font-size: 1.1rem; font-weight: 700; color: #06b6d4; }
h1 {
  font-size: 1.4rem;
  font-weight: 700;
  text-align: center;
  margin-bottom: 6px;
}
.subtitle {
  text-align: center;
  color: #64748b;
  font-size: 0.9rem;
  margin-bottom: 32px;
}
.field { margin-bottom: 18px; }
label {
  display: block;
  font-size: 0.8rem;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 6px;
  font-weight: 600;
}
input {
  width: 100%;
  background: #0d1117;
  border: 1px solid #1f2937;
  border-radius: 8px;
  padding: 12px 14px;
  color: #e2e8f0;
  font-size: 1rem;
  font-family: "DM Sans", sans-serif;
  transition: border-color 0.2s;
}
input:focus {
  outline: none;
  border-color: #06b6d4;
}
.btn-login {
  width: 100%;
  background: #06b6d4;
  color: #000;
  border: none;
  border-radius: 8px;
  padding: 13px;
  font-size: 1rem;
  font-weight: 700;
  cursor: pointer;
  font-family: "DM Sans", sans-serif;
  margin-top: 8px;
  transition: background 0.2s;
}
.btn-login:hover { background: #22d3ee; }
.error-msg {
  background: rgba(239,68,68,0.1);
  border: 1px solid rgba(239,68,68,0.3);
  color: #ef4444;
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 0.88rem;
  margin-bottom: 18px;
  text-align: center;
}
.hint {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #1f2937;
  text-align: center;
  font-size: 0.8rem;
  color: #475569;
}
.hint code {
  background: #1a2035;
  padding: 2px 8px;
  border-radius: 4px;
  color: #94a3b8;
  font-size: 0.78rem;
}
.badge {
  display: inline-block;
  background: rgba(6,182,212,0.1);
  color: #06b6d4;
  border: 1px solid rgba(6,182,212,0.3);
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 0.72rem;
  letter-spacing: 1px;
  text-transform: uppercase;
  margin-bottom: 16px;
}
.center { text-align: center; }
</style>
</head>
<body>
<div class="login-wrap">
  <div class="login-card">
    <div class="logo">
      <div class="dot"></div>
      <div class="logo-text">Clinical AI</div>
    </div>
    <div class="center"><div class="badge">Secure Access</div></div>
    <h1>Doctor Login</h1>
    <p class="subtitle">AI for Real-Time Clinical Decision Support</p>

    <!-- ERROR -->

    <form method="POST" action="/login">
      <div class="field">
        <label>Username</label>
        <input type="text" name="username" placeholder="Enter username" required autofocus>
      </div>
      <div class="field">
        <label>Password</label>
        <input type="password" name="password" placeholder="Enter password" required>
      </div>
      <button type="submit" class="btn-login">Sign In</button>
    </form>

    <div class="hint">
      Demo credentials &nbsp;|&nbsp;
      Username: <code>doctor</code> &nbsp;
      Password: <code>clinical2026</code>
    </div>
  </div>
</div>
</body>
</html>'''

Path('src/dashboard/login.html').write_text(html, encoding='utf-8')
print('login.html written OK')