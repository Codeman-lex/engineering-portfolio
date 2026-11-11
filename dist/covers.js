// Editorial studies of real examples from the project datasets.
function projectCover(slug) {
  if (slug === "veritas") {
    return `<div class="jacket proof"><div class="jacket-head"><span>Veritas</span><small>Evaluation laboratory</small></div>
      <div class="proof-sheet"><div class="proof-running">INVOICE EXTRACT <span>INV-1001</span></div><p>Invoice total</p><div class="proof-answer"><del>140</del> <ins>130</ins><small>USD</small></div><div class="proof-note">↳ Verified against source invoice</div></div>
      <div class="jacket-foot"><span>Field-level evidence</span><span>A / B</span></div></div>`;
  }
  if (slug === "aegis") {
    return `<div class="jacket archive"><div class="jacket-head"><span>Aegis</span><small>Onboarding registry</small></div>
      <div class="archive-folder"><span class="folder-tab">CASE 0040</span><div class="archive-sheet"><div class="archive-line">Business registration</div><strong>Fenn Works</strong><p>Declared address<span>Unit 40, Demo Quay</span></p><p>Observed address<span>Unit 0, Demo Quay</span></p><i>Requires review</i></div></div>
      <div class="jacket-foot"><span>Synthetic case file</span><span>0040</span></div></div>`;
  }
  return `<div class="jacket monitor"><div class="jacket-head"><span>Sentinel AI</span><small>Risk intelligence</small></div>
    <div class="scope"><i></i><b></b><em></em><span class="signal-point"></span></div><div class="monitor-reading"><small>FLAGGED EXPOSURE</small><strong>$2.73M</strong><span>5,580 flagged transactions</span></div>
    <div class="jacket-foot"><span>Synthetic ledger</span><span>100,000 transactions</span></div></div>`;
}
