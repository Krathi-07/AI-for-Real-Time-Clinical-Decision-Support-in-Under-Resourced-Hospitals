import py_compile
import shutil
import tempfile
from pathlib import Path

MAIN = Path("src/api/main.py")
text = MAIN.read_text(encoding="utf-8")

# Replace the button onclick with an inline definition
# that doesn't rely on a separate script block
OLD_BTN = "      <button onclick='analyseNote()'"
NEW_BTN = """      <button onclick='(async function(){
        var note=document.getElementById("clinicalNote").value.trim();
        if(!note){alert("Please enter a note.");return;}
        this.textContent="Analysing...";this.disabled=true;
        try{
          var pid=window.location.pathname.split("/").pop();
          var r=await fetch("/analyse-note/"+pid,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({note:note})});
          var d=await r.json();
          var res=document.getElementById("noteResults");
          if(d.error){res.innerHTML="<p style=color:#ef4444>"+d.error+"</p>";res.style.display="block";return;}
          function ch(a,c){return a&&a.length?a.map(x=>"<span style=background:"+c+"20;color:"+c+";padding:.2rem .6rem;border-radius:12px;font-size:.78rem;margin:.1rem;display:inline-block>"+x+"</span>").join(""):"<span style=color:#94a3b8;font-size:.8rem>None</span>";}
          var vt=d.vitals&&Object.keys(d.vitals).length?Object.entries(d.vitals).map(([k,v])=>"<span style=background:#f0fdf420;color:#16a34a;padding:.2rem .6rem;border-radius:12px;font-size:.78rem;margin:.1rem;display:inline-block>"+k+": "+v+"</span>").join(""):"<span style=color:#94a3b8;font-size:.8rem>None</span>";
          res.innerHTML="<div style=display:grid;grid-template-columns:1fr_1fr;gap:.75rem>"+
            "<div><p style=font-size:.75rem;font-weight:700;color:#94a3b8;margin-bottom:.3rem>SYMPTOMS/DISEASES</p>"+ch((d.symptoms||[]).concat(d.diagnoses||[]),"#6c3fcf")+"</div>"+
            "<div><p style=font-size:.75rem;font-weight:700;color:#94a3b8;margin-bottom:.3rem>MEDICATIONS</p>"+ch(d.medications||[],"#0ea5e9")+"</div>"+
            "<div><p style=font-size:.75rem;font-weight:700;color:#94a3b8;margin-bottom:.3rem>VITALS</p>"+vt+"</div>"+
            "<div><p style=font-size:.75rem;font-weight:700;color:#94a3b8;margin-bottom:.3rem>NEGATED</p>"+ch(d.negated||[],"#94a3b8")+"</div></div>"+
            "<p style=font-size:.72rem;color:#64748b;margin-top:.5rem>Confidence: "+(d.confidence||"n/a")+" | Entities: "+(d.entity_count||0)+"</p>";
          res.style.display="block";
        }catch(e){document.getElementById("noteResults").innerHTML="<p style=color:#ef4444>"+e+"</p>";document.getElementById("noteResults").style.display="block";}
        finally{this.textContent="⚡ Analyse Note";this.disabled=false;}
      }).call(this)'"""

if OLD_BTN in text:
    text = text.replace(OLD_BTN, NEW_BTN)
    print("✅  Button replaced with inline async function")
else:
    print("❌  Button pattern not found")

MAIN.write_text(text, encoding="utf-8")
tmp = Path(tempfile.mktemp(suffix=".py"))
shutil.copy(MAIN, tmp)
try:
    py_compile.compile(str(tmp), doraise=True)
    print("✅  Syntax check PASSED")
except py_compile.PyCompileError as e:
    print(f"❌  {e}")
finally:
    tmp.unlink(missing_ok=True)
