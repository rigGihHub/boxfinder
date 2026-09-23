import IntakeWizard from "./IntakeWizard";
const API=process.env.NEXT_PUBLIC_API_URL||"http://localhost:8000";

export default function IntakePage(){
  return <main className="intakePage">
    <header className="nav sourceNav">
      <a className="brand" href="/"><span className="brandMark">BF</span><span>BOXFINDER<small>CHASE SMARTER</small></span></a>
      <nav><a href="/admin/source-hub">Datakällor</a><a href="/admin/catalog">Produktkö</a><a href="/admin/intake">Koppla butik</a><a href="/admin/intake/batch">Batch</a><a href="/admin/activation">Aktiveringskö</a></nav>
      <span className="version">v0.45.1</span>
    </header>
    <section className="intakeHero">
      <span className="kicker">STORE INTAKE PIPELINE</span>
      <h1>Koppla en butik<br/><em>utan specialkod.</em></h1>
      <p>Klistra in ett prov från butikens CSV- eller JSON-feed. BoxFinder försöker identifiera produkt-ID, namn, pris, lager, länk och preorder-fält och visar resultatet innan något aktiveras.</p>
    </section>
    <IntakeWizard api={API}/>
  </main>
}
