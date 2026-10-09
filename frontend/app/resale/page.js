import {Suspense} from "react";
import ResalePageClient from "../components/ResalePageClient";
import {buildLabel} from "../lib/build";

export const dynamic = "force-dynamic";

export default function ResalePage() {
  return <Suspense fallback={<main className="resalePage"><div className="chaseEmpty"><b>BoxFinder laddar sökningen…</b></div></main>}>
    <ResalePageClient version={buildLabel()}/>
  </Suspense>;
}
