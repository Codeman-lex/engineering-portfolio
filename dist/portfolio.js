const main = document.querySelector("main");
const chapters = {overview:"Walkthrough",build:"Engineering",results:"Results",replicate:"Reproduce",next:"Next iteration"};
function route(p, section="overview"){return "#project/"+p.slug+"/"+section}
function tags(p){return p.tools.map(t=>'<span>'+t+'</span>').join("")}
function projectLinks(p) {
  const app = "https://codeman-lex.github.io/engineering-portfolio/"+p.slug+"/";
  const code = "https://github.com/Codeman-lex/engineering-portfolio/tree/main/projects/"+p.slug;
  return `<div class="project-links"><a href="${app}" target="_blank" rel="noopener">View project ↗</a><a href="${code}" target="_blank" rel="noopener">View code ↗</a></div>`;
}
function index(){
  document.title="Engineering portfolio · Vincent Chinemerem";
  const invitations = {
    "sentinel-ai": ["Fraud signals", "How many false alerts would you accept to catch one more suspicious payment?", "Compare detection methods", "results"],
    veritas: ["Answer grading", "The invoice says $130. The answer says $140. How much credit does it deserve?", "Grade the answer", "overview"],
    aegis: ["Case review", "The applicant says Unit 4. The document says Unit 0. Would you approve the case?", "Review the evidence", "overview"]
  };
  main.innerHTML=`<section class="studio-opening"><div class="studio-sign">Vincent Chinemerem</div><h1>Engineering<br><em>portfolio.</em></h1><p>I build intelligent systems that turn complex problems into practical software.</p></section>
  <section class="shelf" aria-label="Interactive projects">${projects.map(p=>{
    const invitation=invitations[p.slug];
    return `<article><a class="cover-link" href="${route(p)}" aria-label="Explore ${p.name}">${projectCover(p.slug)}</a><div class="shelf-copy"><span>${p.field}</span><h2>${invitation?.[1] || p.name}</h2>${projectLinks(p)}<a href="${route(p)}">Read case study ↗</a></div></article>`;
  }).join("")}</section>
  <section id="about" class="chapter"><h2>About</h2><p>My background spans business analysis, financial technology, compliance and data analytics. I use AI-assisted development to explore where software can help people investigate a signal, check an answer or review a decision.</p></section>
  <section id="contact" class="chapter"><h2>Contact</h2><p><a href="https://github.com/Codeman-lex/engineering-portfolio/tree/main/dist">View the source on GitHub ↗</a></p></section>`;

}
function entries(items){
  return items.map(([label,body])=>`<div class="entry"><h3>${label}</h3><p>${body}</p></div>`).join("");
}
function gallery(p){
  return `<div class="switcher" aria-label="Application screens">${p.pictures.map((pic,i)=>`<button data-picture="${i}" aria-pressed="${i===0}">${pic.name}</button>`).join("")}</div>
  <figure><a id="full-image" target="_blank" rel="noopener"><img id="capture" alt=""></a><figcaption id="caption"></figcaption></figure>`;
}
function showPicture(p,i){
  const pic=p.pictures[i], img=main.querySelector("#capture");
  img.src=pic.src;img.alt=p.name+" – "+pic.name;
  main.querySelector("#full-image").href=pic.src;
  main.querySelector("#caption").textContent=pic.caption;
  main.querySelectorAll("[data-picture]").forEach((b,j)=>b.setAttribute("aria-pressed",j===i));
}
function showResult(p,i){
  const ev=p.evaluation,m=ev.methods[i];
  main.querySelector("#comparison").innerHTML=`<p>${m.cutoff}</p><div class="result-stats"><div><strong>${m.tp}</strong>positives detected</div><div><strong>${ev.positives-m.tp}</strong>positives missed</div><div><strong>${m.fp}</strong>false alerts</div></div><p>${(100*m.tp/(m.tp+m.fp)).toFixed(1)}% precision · ${(100*m.tp/ev.positives).toFixed(1)}% recall</p>`;
  main.querySelectorAll("[data-method]").forEach((b,j)=>b.setAttribute("aria-pressed",j===i));
}
function caseStudy(p,chapter){
  document.title=p.name+" · "+chapters[chapter]+" · Codeman Lex";
  main.innerHTML=`<a class="back" href="#work">← Project index</a><div class="case-head"><div><span class="field">${p.field}</span><h1>${p.name}</h1></div><p>${p.summary}</p></div>
  ${projectLinks(p)}<nav class="chapters" aria-label="Case study sections">${Object.entries(chapters).map(([key,name])=>`<a href="${route(p,key)}" ${key===chapter?'aria-current="page"':''}>${name}</a>`).join("")}</nav><section class="chapter"></section>`;
  const panel=main.querySelector(".chapter");
  if(chapter==="overview"){
    panel.innerHTML=`<div class="story"><div><h2>The problem</h2><p>${p.problem}</p></div><div><h2>What I built</h2><p>${p.contribution}</p></div></div>${gallery(p)}`;
    showPicture(p,0);
    showExercise(panel,p.slug);
    panel.querySelectorAll("[data-picture]").forEach((btn,i)=>btn.onclick=()=>showPicture(p,i));
  }else if(chapter==="build"){
    panel.innerHTML=`<h2>How the system works</h2><ol class="flow">${(p.flow||["Seeded ledger","Prior activity","Detection engines","Investigation"]).map(step=>"<li>"+step+"</li>").join("")}</ol><div class="tags">${tags(p)}</div>${entries(p.decisions)}<p class="note">${p.credit}</p>`;
  }else if(chapter==="results"){
    if(Array.isArray(p.evaluation)){
      panel.innerHTML='<h2>What the tests showed</h2>'+entries(p.evaluation);
      return;
    }
    panel.innerHTML=`<h2>What the tests showed</h2><p>${p.evaluation.context}</p><div class="switcher">${p.evaluation.methods.map((m,i)=>`<button data-method="${i}">${m.name}</button>`).join("")}</div><div id="comparison" aria-live="polite"></div><p>${p.evaluation.takeaway}</p><p class="note">${p.limits}</p>`;
    showResult(p,0);
    panel.querySelectorAll("[data-method]").forEach((btn,i)=>btn.onclick=()=>showResult(p,i));
  }else if(chapter==="replicate"){
    panel.innerHTML=`<h2>Run it yourself</h2><p>${p.reproduceIntro}</p><a class="primary" download href="${p.source}">Download source ZIP ↓</a><h3>Install, test and launch</h3><pre><code></code></pre><h3>Check your result</h3><p>${p.verify}</p>`;
    panel.querySelector("code").textContent=p.commands;
  }else{
    panel.innerHTML=`<h2>What I would improve</h2><p>${p.limits}</p>${entries(p.next)}`;
  }
}
function render(){
  const [,slug,chapter]=location.hash.slice(1).split("/");
  const p=projects.find(project=>project.slug===slug);
  document.body.dataset.project=p?.slug || "";
  if(p)caseStudy(p,Object.hasOwn(chapters,chapter)?chapter:"overview");else index();
}
render();
if(['#about','#contact'].includes(location.hash)) document.querySelector(location.hash).scrollIntoView();
window.addEventListener("hashchange",()=>{render();main.focus({preventScroll:true});(document.querySelector(["#contact","#about"].includes(location.hash)?location.hash:"main")).scrollIntoView()});
