# fix_toggle.py

with open("src/api/main.py", "r", encoding="utf-8", errors="replace") as f:
    content = f.read()

OLD = """<script>
(function(){{
  var t=localStorage.getItem('theme')||(window.matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light');
  document.documentElement.setAttribute('data-theme',t);
  var btn=document.getElementById('themeBtn');
  if(btn)btn.textContent=t==='dark'?'&#9728; Light':'&#127769; Dark';
}})();
function toggleTheme(){{
  var t=document.documentElement.getAttribute('data-theme')==='dark'?'light':'dark';
  document.documentElement.setAttribute('data-theme',t);
  localStorage.setItem('theme',t);
  var btn=document.getElementById('themeBtn');
  if(btn)btn.textContent=t==='dark'?'&#9728; Light':'&#127769; Dark';
}}
</script>"""

NEW = """<script>
(function(){{
  var t=localStorage.getItem('theme')||(window.matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light');
  document.documentElement.setAttribute('data-theme',t);
  document.addEventListener('DOMContentLoaded',function(){{
    var btn=document.getElementById('themeBtn');
    if(btn)btn.textContent=t==='dark'?'Light Mode':'Dark Mode';
  }});
}})();
function toggleTheme(){{
  var t=document.documentElement.getAttribute('data-theme')==='dark'?'light':'dark';
  document.documentElement.setAttribute('data-theme',t);
  localStorage.setItem('theme',t);
  var btn=document.getElementById('themeBtn');
  if(btn)btn.textContent=t==='dark'?'Light Mode':'Dark Mode';
}}
</script>"""

if OLD not in content:
    print("ERROR: script block not found")
    # show what's actually there
    idx = content.find("toggleTheme")
    print(repr(content[idx:idx+400]))
else:
    content = content.replace(OLD, NEW, 1)
    with open("src/api/main.py", "w", encoding="utf-8", errors="xmlcharrefreplace") as f:
        f.write(content)
    print("SUCCESS: Toggle script fixed.")
    