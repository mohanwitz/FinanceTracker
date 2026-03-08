import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

const CATEGORIES = [
  "Food & Dining", "Shopping", "Housing", "Transportation", "Vehicle", 
  "Life & Entertainment", "Communication, PC", "Financial expenses", "Investments", "Income", "Other"
];

export async function parseEmailToTransaction(subject: string, body: string) {
  const systemPrompt = `You are a financial transaction parser. Given the subject and body of a transaction/alert email, extract structured data.
Respond with a single JSON object only, no other text. Use exactly these keys:
- "transaction_date": date of the transaction in YYYY-MM-DD format (use the date from the email; if missing, use today)
- "amount": numeric amount spent (positive number; if it's a credit/refund use a negative number)
- "merchant": short name of the vendor/merchant/description
- "category": exactly one of: ${JSON.stringify(CATEGORIES)}

If the email does not describe a single clear transaction, set "amount" to null and "merchant" to a short summary. Category must still be one of the list; use "Other" if unclear.
Output only valid JSON.`;

  const content = `Subject: ${subject}\n\n${body}`;

  try {
    const response = await openai.chat.completions.create({
      model: "gpt-4o-mini",
      messages: [
        { role: "system", content: systemPrompt },
        { role: "user", content: content.substring(0, 12000) }
      ],
      temperature: 0,
      response_format: { type: "json_object" }
    });

    const parsed = JSON.parse(response.choices[0].message.content || '{}');
    return parsed;
  } catch (error) {
    console.error("Failed to parse email", error);
    return null;
  }
}