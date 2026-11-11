// Compact, resettable case-study exercises. The Python source downloads contain the full labs.
function showExercise(panel,slug){
  const demo=document.createElement("section");
  demo.className="exercise";
  if(slug==="veritas"){
    demo.innerHTML='<h3>Grade an invoice answer</h3><p>Source invoice INV-1001 records a total of 130 USD. Edit the candidate JSON and move the passing threshold.</p><label>Candidate response<textarea rows="3">{"invoice":"INV-1001","total":140}</textarea></label><label>Pass threshold <input type="range" min="0" max="100" value="100"></label><output aria-live="polite"></output>';
    const update=()=>{
      let obj;
      try{obj=JSON.parse(demo.querySelector("textarea").value)}catch{obj=null}
      const checks=[["Exact schema",!!obj && Object.keys(obj).sort().join(",")==="invoice,total"],["Invoice matches",obj?.invoice==="INV-1001"],["Total matches",obj?.total===130]];
      const score=Math.round(checks.filter(x=>x[1]).length/3*10000)/100;
      const threshold=Number(demo.querySelector("input").value);
      demo.querySelector("output").textContent=checks.map(([l,ok])=>(ok?"✓ ":"✕ ")+l).join(" · ")+"\n"+score+" / 100 · "+(score>=threshold?"Pass":"Fail")+" at "+threshold;
    };
    demo.oninput=update;update();
  } else if(slug==="aegis"){
    demo.innerHTML='<h3>Resolve an address mismatch</h3><p>The fictional applicant declared Unit 4, Demo Quay. Check the submitted address, correct it and record a decision. This exercise resets when you leave the page.</p><label>Document address<input value="Unit 0, Demo Quay"></label><label>Decision reason<input placeholder="Explain your review"></label><div class="switcher"><button>Validate documents</button><button>Approve case</button><button>Request information</button></div><output aria-live="polite"></output>';
    let validated=false,closed=false;
    const log=["Intake received · document address differs from declaration."];
    const out=demo.querySelector("output"),[address,reason]=demo.querySelectorAll("input");
    const [check,approve,request]=demo.querySelectorAll("button");
    function display(){out.textContent=log.join("\n");approve.disabled=closed||!validated||!reason.value.trim();request.disabled=closed||!reason.value.trim();check.disabled=closed;address.disabled=closed}
    check.onclick=()=>{validated=address.value.trim()==="Unit 4, Demo Quay";log.push(validated?"Validation passed · declared and observed addresses match.":"Review required · expected Unit 4, Demo Quay; observed "+(address.value.trim()||"(missing)")+".");display()};
    address.oninput=()=>{validated=false;display()};reason.oninput=display;
    approve.onclick=()=>{closed=true;log.push("Approved · "+reason.value.trim());display()};
    request.onclick=()=>{validated=false;log.push("Information requested · "+reason.value.trim());display()};display();
  }else return;
  panel.prepend(demo);
}
