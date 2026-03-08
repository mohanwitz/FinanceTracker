import { auth } from "@/lib/auth";
import { fetchRecentEmails } from "@/lib/gmail";
import { parseEmailToTransaction } from "@/lib/parser";
import { prisma } from "@/lib/prisma";
import { NextResponse } from "next/server";

export async function POST() {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const userId = session.user.id;

  try {
    const emails = await fetchRecentEmails(userId);
    let insertedCount = 0;

    for (const email of emails) {
      // Check if we already processed this message
      const existing = await prisma.transaction.findUnique({
        where: { userId_messageId: { userId, messageId: email.id } }
      });

      if (existing) continue;

      const parsed = await parseEmailToTransaction(email.subject, email.body);
      
      if (parsed) {
        await prisma.transaction.create({
          data: {
            userId,
            messageId: email.id,
            transactionDate: parsed.transaction_date || new Date().toISOString().split('T')[0],
            amount: parsed.amount ?? null,
            merchant: parsed.merchant || "Unknown",
            category: parsed.category || "Other",
            rawSubject: email.subject.substring(0, 500),
            needsReview: parsed.amount === null
          }
        });
        insertedCount++;
      }
    }

    return NextResponse.json({ success: true, inserted: insertedCount });
  } catch (error) {
    console.error("Sync error:", error);
    return NextResponse.json({ error: "Failed to sync" }, { status: 500 });
  }
}