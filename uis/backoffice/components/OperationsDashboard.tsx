"use client";

import { useMemo } from "react";
import {
  sampleLocations,
  sampleMenuItems,
  sampleSales,
  sampleWasteRecords,
} from "../../../src/data/sampleOperations";
import type {
  Location,
  MenuItem,
  SaleTransaction,
  WasteRecord,
} from "../../../src/types/models";
import { getOperationsSnapshot } from "@/lib/operationsSnapshot";
import { MetricCard } from "./MetricCard";

const usd = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

type OperationsDashboardProps = {
  sales?: SaleTransaction[];
  locations?: Location[];
  menuItems?: MenuItem[];
  wasteRecords?: WasteRecord[];
};

export function OperationsDashboard({
  sales = sampleSales,
  locations = sampleLocations,
  menuItems = sampleMenuItems,
  wasteRecords = sampleWasteRecords,
}: OperationsDashboardProps) {
  const snapshot = useMemo(
    () => getOperationsSnapshot(sales, locations, menuItems, wasteRecords),
    [sales, locations, menuItems, wasteRecords],
  );

  return (
    <>
      <section className="metric-grid" aria-label="Operations summary">
        <MetricCard
          label="Recorded revenue"
          value={usd.format(snapshot.totalRevenue)}
          detail={`${snapshot.saleCount} sample transactions across two markets`}
          tone="positive"
        />
        <MetricCard
          label="Average ticket"
          value={usd.format(snapshot.averageTicket)}
          detail="Combined Colombia and Florida sample"
        />
        <MetricCard
          label="Waste exposure"
          value={usd.format(snapshot.wasteCost)}
          detail="Ingredient cost requiring attention"
          tone="warning"
        />
        <MetricCard
          label="Active locations"
          value="14"
          detail="10 in Colombia · 4 in Florida"
        />
      </section>

      <div className="dashboard-grid">
        <section className="panel performance-panel">
          <div className="panel-heading">
            <div>
              <p className="kicker">Location intelligence</p>
              <h2>Performance snapshot</h2>
            </div>
            <span className="live-pill">Milestone 2 logic</span>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Location</th>
                  <th>Market</th>
                  <th>Margin</th>
                  <th>Score</th>
                </tr>
              </thead>
              <tbody>
                {snapshot.locations.map(({ location, score, margin }) => (
                  <tr key={location.id}>
                    <td>
                      <strong>{location.name}</strong>
                      <span>{location.manager}</span>
                    </td>
                    <td>{location.country}</td>
                    <td>{margin.toFixed(1)}%</td>
                    <td>
                      <div className="score">
                        <span style={{ width: `${score}%` }} />
                      </div>
                      <small>{score.toFixed(1)}</small>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <aside className="panel top-items">
          <div className="panel-heading">
            <div>
              <p className="kicker">Menu pulse</p>
              <h2>Top sellers</h2>
            </div>
          </div>
          <ol>
            {snapshot.topItems.map(({ item, totalSold }, index) => (
              <li key={item.id}>
                <span className="rank">0{index + 1}</span>
                <div>
                  <strong>{item.name}</strong>
                  <span>{item.category}</span>
                </div>
                <b>{totalSold}</b>
              </li>
            ))}
          </ol>
          <p className="data-note">
            Visible output is calculated at render time from the canonical
            module in the monorepo root.
          </p>
        </aside>
      </div>
    </>
  );
}
