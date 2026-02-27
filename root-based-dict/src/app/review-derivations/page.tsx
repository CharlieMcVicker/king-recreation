import { getConnections, getDefinitions } from "@/lib/data";
import ReviewDerivations from "@/components/ReviewDerivations";

export default async function ReviewDerivationsPage() {
  const connections = await getConnections();

  // Fetch definitions for all connections
  const connectionsWithDefinitions = await Promise.all(
    connections.map(async (conn) => {
      const fromDefinitions = await getDefinitions(conn.from_corpus_ids);
      const toDefinitions = await getDefinitions(conn.to_corpus_ids);
      return {
        ...conn,
        from_definitions: fromDefinitions,
        to_definitions: toDefinitions,
      };
    }),
  );

  return (
    <div className="container mx-auto p-4">
      <ReviewDerivations initialConnections={connectionsWithDefinitions} />
    </div>
  );
}
