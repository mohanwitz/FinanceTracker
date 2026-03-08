import { auth, signIn, signOut } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { SyncButton } from "@/components/SyncButton";

export default async function Home() {
  const session = await auth();

  if (!session?.user) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center p-24">
        <h1 className="text-4xl font-bold mb-8">Finance Tracker</h1>
        <form action={async () => { "use server"; await signIn("google"); }}>
          <button className="bg-blue-500 text-white px-6 py-2 rounded-md">Sign in with Google</button>
        </form>
      </main>
    );
  }

  const transactions = await prisma.transaction.findMany({
    where: { userId: session.user.id },
    orderBy: { transactionDate: 'desc' }
  });

  return (
    <main className="min-h-screen p-8 max-w-5xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <div className="flex gap-4 items-center">
          <SyncButton />
          <form action={async () => { "use server"; await signOut(); }}>
            <button className="text-sm text-gray-500">Sign Out</button>
          </form>
        </div>
      </div>

      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Recent Transactions</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b">
                <th className="py-2">Date</th>
                <th className="py-2">Merchant</th>
                <th className="py-2">Category</th>
                <th className="py-2 text-right">Amount</th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((t) => (
                <tr key={t.id} className="border-b last:border-0">
                  <td className="py-3">{t.transactionDate}</td>
                  <td className="py-3">{t.merchant}</td>
                  <td className="py-3">
                    <span className="px-2 py-1 bg-gray-100 rounded-full text-xs">
                      {t.category}
                    </span>
                  </td>
                  <td className="py-3 text-right">
                    {t.amount !== null ? `$${t.amount.toFixed(2)}` : 'N/A'}
                  </td>
                </tr>
              ))}
              {transactions.length === 0 && (
                <tr>
                  <td colSpan={4} className="py-4 text-center text-gray-500">No transactions found. Click Sync to fetch from Gmail.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </main>
  );
}