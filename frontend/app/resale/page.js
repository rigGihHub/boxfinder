import {Suspense} from "react";
import ResalePageClient from "../components/ResalePageClient";

export default function ResalePage() {
  return <Suspense fallback={<main className="resalePage"><div className="chaseEmpty"><b>BoxFinder laddar sökningen…</b></div></main>}>
    <ResalePageClient/>
  </Suspense>;
}
