import React, { useEffect, useState } from "react";
import {
  Search,
  Building2,
  User,
  Calendar,
  Factory,
  Mail,
  Phone,
  MapPin,
  ExternalLink,
} from "lucide-react";
import { api } from "../api";
import { Card, Badge, Spinner, Empty, Field } from "./ui";

export default function Organizations() {
  const [q, setQ] = useState("");
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  async function load(query = "") {
    setLoading(true);
    setError(null);
    try {
      setItems(await api.organizations(query));
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  function onSubmit(e) {
    e.preventDefault();
    load(q.trim());
  }

  return (
    <div className="space-y-6">
      <Card className="p-5">
        <div className="mb-1 flex items-center gap-2">
          <h2 className="text-lg font-bold text-slate-800">Strukturirani podatki (relacijska baza)</h2>
        </div>
        <p className="mb-4 text-sm text-slate-500">
          Metapodatki, ki jih je iz besedila izluščila generativna UI in shranila v MySQL.
          Iskanje deluje po imenu, panogi, dejavnosti, vodstvu in povzetku.
        </p>
        <form onSubmit={onSubmit} className="flex gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Išči po ključnih besedah ..."
              className="w-full rounded-xl border border-slate-200 py-2.5 pl-10 pr-4 text-sm outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
            />
          </div>
          <button
            type="submit"
            className="rounded-xl bg-gradient-to-r from-indigo-500 to-violet-500 px-5 text-sm font-semibold text-white"
          >
            Išči
          </button>
        </form>
      </Card>

      {loading ? (
        <div className="flex justify-center py-16">
          <Spinner className="h-6 w-6 text-indigo-500" />
        </div>
      ) : error ? (
        <p className="text-sm text-red-600">{error}</p>
      ) : items.length === 0 ? (
        <Empty
          icon={Building2}
          title="Ni organizacij"
          hint="Zaženi obdelavo na nadzorni plošči, da napolniš bazo."
        />
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          {items.map((org) => (
            <Card key={org.id} className="p-6">
              <div className="mb-4 flex items-start justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="rounded-xl bg-gradient-to-br from-indigo-500 to-violet-500 p-2.5 text-white">
                    <Building2 className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-800">{org.name}</h3>
                    {org.industry && <Badge color="violet">{org.industry}</Badge>}
                  </div>
                </div>
                <a
                  href={org.source_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-slate-400 hover:text-indigo-500"
                  title="Odpri vir"
                >
                  <ExternalLink className="h-4 w-4" />
                </a>
              </div>

              {org.summary && (
                <p className="mb-4 text-sm leading-relaxed text-slate-600">{org.summary}</p>
              )}

              <div className="grid grid-cols-2 gap-4 border-t border-slate-100 pt-4">
                <Field label={<><User className="mr-1 inline h-3 w-3" />Vodstvo</>}>{org.ceo}</Field>
                <Field label={<><Calendar className="mr-1 inline h-3 w-3" />Ustanovljeno</>}>{org.founded_year}</Field>
                <Field label={<><Factory className="mr-1 inline h-3 w-3" />Dejavnost</>}>{org.main_activity}</Field>
                <Field label={<><Mail className="mr-1 inline h-3 w-3" />E-pošta</>}>{org.email}</Field>
                <Field label={<><Phone className="mr-1 inline h-3 w-3" />Telefon</>}>{org.phone}</Field>
                <Field label={<><MapPin className="mr-1 inline h-3 w-3" />Naslov</>}>{org.address}</Field>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
