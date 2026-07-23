import {
  sampleLocations,
  sampleMenuItems,
  sampleSales,
  sampleWasteRecords,
} from "../../../../src/data/sampleOperations";
import {
  calculateAverageTicket,
  calculateCountryComparison,
  calculateLocationMargin,
  calculateWasteCost,
  findTopSellingItems,
  rankLocationsByPerformance,
} from "../../../../src/utils/transformations";
import { MetricCard } from "./MetricCard";

const usd = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

export function OperationsDashboard() {
  const averageTicket = calculateAverageTicket(sampleSales, "USD");
  const wasteCost = sampleLocations.reduce(
    (total, location) =>
      total +
      calculateWasteCost(sampleWasteRecords, location.id, "USD"),
    0,
  );
  const comparison = calculateCountryComparison(
    sampleSales,
    sampleLocations,
    sampleMenuItems,
  );
  const ranking = rankLocationsByPerformance(
    sampleLocations,
    sampleSales,
    sampleWasteRecords,
    sampleMenuItems,
  );
  const topItems = findTopSellingItems(sampleSales, sampleMenuItems, 3);
  const totalRevenue =
    comparison.Colombia.totalRevenue.USD + comparison.USA.totalRevenue.USD;

  return (
    <>
      <section className="metric-grid" aria-label="Operations summary">
        <MetricCard
          label="Recorded revenue"
          value={usd.format(totalRevenue)}
          detail={`${sampleSales.length} sample transactions across two markets`}
          tone="positive"
        />
        <MetricCard
          label="Average ticket"
          value={usd.format(averageTicket)}
          detail="Combined Colombia and Florida sample"
        />
        <MetricCard
          label="Waste exposure"
          value={usd.format(wasteCost)}
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
                {ranking.map(({ location, score }) => (
                  <tr key={location.id}>
                    <td>
                      <strong>{location.name}</strong>
                      <span>{location.manager}</span>
                    </td>
                    <td>{location.country}</td>
                    <td>
                      {calculateLocationMargin(
                        sampleSales,
                        sampleMenuItems,
                        location.id,
                        "USD",
                      ).toFixed(1)}
                      %
                    </td>
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
            {topItems.map(({ item, totalSold }, index) => (
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
