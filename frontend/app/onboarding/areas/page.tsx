"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AppNav } from "@/components/AppNav";
import { SakuraSanctuary } from "@/components/SakuraSanctuary";
import {
  CatalogArea,
  SelectedArea,
  completeOnboarding,
  createArea,
  listAreas,
  removeArea,
  selectArea,
} from "@/lib/api";

export default function OnboardingAreasPage() {
  const router = useRouter();
  const [catalog, setCatalog] = useState<CatalogArea[]>([]);
  const [selected, setSelected] = useState<SelectedArea[]>([]);
  const [custom, setCustom] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function load() {
    const data = await listAreas();
    setCatalog(data.catalog);
    setSelected(data.selected);
  }

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : "Could not load areas"));
  }, []);

  async function toggle(area: CatalogArea) {
    setError("");
    try {
      if (area.selected) {
        const match = selected.find((item) => item.area_id === area.id);
        if (match) await removeArea(match.id);
      } else {
        await selectArea(area.id);
      }
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not update areas");
    }
  }

  async function addCustom(event: FormEvent) {
    event.preventDefault();
    if (!custom.trim()) return;
    setError("");
    try {
      await createArea(custom.trim());
      setCustom("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create area");
    }
  }

  async function continueOnboarding() {
    if (selected.length === 0) {
      setError("Pick at least one part of life.");
      return;
    }
    setBusy(true);
    try {
      await completeOnboarding();
      router.push("/today");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not continue");
      setBusy(false);
    }
  }

  return (
    <main className="shell lifemap-room">
      <AppNav active="map" />
      <SakuraSanctuary variant="edge" bloom={55} />
      <p className="eyebrow">Life map</p>
      <h1>Hello. What do you want to grow?</h1>
      <p className="lede">
        Health, study, money, career — or a name of your own. You can add more later.
      </p>
      <div className="row" style={{ marginTop: 28 }}>
        {catalog.map((area) => (
          <button
            key={area.id}
            type="button"
            className={area.selected ? "chip on" : "chip"}
            onClick={() => toggle(area)}
          >
            {area.name}
          </button>
        ))}
      </div>
      {selected.filter((item) => item.is_custom).length > 0 ? (
        <div className="row" style={{ marginTop: 12 }}>
          {selected
            .filter((item) => item.is_custom)
            .map((item) => (
              <button key={item.id} type="button" className="chip on" onClick={() => removeArea(item.id).then(load)}>
                {item.name}
              </button>
            ))}
        </div>
      ) : null}
      <form className="row" style={{ marginTop: 28 }} onSubmit={addCustom}>
        <input
          placeholder="Create your own area"
          value={custom}
          onChange={(e) => setCustom(e.target.value)}
          style={{ flex: 1, minWidth: 220 }}
        />
        <button type="submit" className="secondary">
          Add
        </button>
      </form>
      {error ? <p className="error">{error}</p> : null}
      <div style={{ marginTop: 32 }}>
        <button type="button" disabled={busy} onClick={continueOnboarding}>
          {busy ? "Saving…" : "Go to Today"}
        </button>
      </div>
    </main>
  );
}
