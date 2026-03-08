const CATEGORIES = [
  "Food & Dining", "Shopping", "Housing", "Transportation", "Vehicle", 
  "Life & Entertainment", "Communication, PC", "Financial expenses", "Investments", "Income", "Other"
];

const CATEGORY_MAP: Record<string, string[]> = {
  "Food & Dining": ["swiggy", "zomato", "uber eats", "starbucks", "mcdonalds", "restaurant"],
  "Shopping": ["amazon", "flipkart", "myntra", "grocery", "supermarket", "reliance"],
  "Transportation": ["uber", "ola", "petrol", "fuel", "metro", "irctc"],
  "Life & Entertainment": ["netflix", "spotify", "pvr", "cinema", "theatre"],
};

interface ParsingRule {
  name: string;
  amountRegex: RegExp;
  merchantRegex: RegExp;
  dateRegex?: RegExp;
}

const PARSING_RULES: ParsingRule[] = [
  {
    name: "CRED Payment",
    amountRegex: /(?:payment|paid)\s+(?:of|for)?\s*(?:Rs\.?|INR|AED|\$)\s*([\d,]+\.?\d*)/i,
    merchantRegex: /(?:to|towards)\s+([A-Z0-9\s\.\*]{2,30})/i,
  },
  {
    name: "Standard Debit",
    amountRegex: /(?:debited|spent|charged)\s+(?:for|of)?\s*(?:Rs\.?|INR|AED|\$)\s*([\d,]+\.?\d*)/i,
    merchantRegex: /(?:at|to|on)\s+([A-Z0-9\s\.\*]{2,30})/i,
  },
  {
    name: "Generic Transaction",
    amountRegex: /(?:Rs\.?|INR|AED|\$)\s*([\d,]+\.?\d*)/i,
    merchantRegex: /(?:at|to|on|via)\s+([A-Z0-9\s\.\*]{2,30})/i,
  }
];

export function parseEmailToTransaction(subject: string, body: string) {
  const combined = `Subject: ${subject}\n\n${body}`;
  
  let amount: number | null = null;
  let merchant = "Unknown";
  let category = "Other";
  let transactionDate = new Date().toISOString().split('T')[0];

  for (const rule of PARSING_RULES) {
    const amountMatch = combined.match(rule.amountRegex);
    const merchantMatch = combined.match(rule.merchantRegex);

    if (amountMatch) {
      amount = parseFloat(amountMatch[1].replace(/,/g, ''));
    }

    if (merchantMatch) {
      merchant = merchantMatch[1].trim();
    }

    if (amount !== null) break;
  }

  // Categorize based on merchant keywords
  const merchantLower = merchant.toLowerCase();
  for (const [cat, keywords] of Object.entries(CATEGORY_MAP)) {
    if (keywords.some(kw => merchantLower.includes(kw))) {
      category = cat;
      break;
    }
  }

  // If we found an amount but couldn't parse much else, it's still a transaction
  if (amount !== null) {
    return {
      transaction_date: transactionDate,
      amount,
      merchant,
      category
    };
  }

  return null;
}
