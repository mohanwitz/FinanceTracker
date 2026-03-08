import { google } from 'googleapis';
import { prisma } from './prisma';

export async function fetchRecentEmails(userId: string) {
  const account = await prisma.account.findFirst({
    where: { userId, provider: 'google' }
  });

  if (!account || !account.access_token) {
    throw new Error('No Google account connected or missing access token');
  }

  const oauth2Client = new google.auth.OAuth2(
    process.env.GOOGLE_CLIENT_ID,
    process.env.GOOGLE_CLIENT_SECRET
  );

  oauth2Client.setCredentials({
    access_token: account.access_token,
    refresh_token: account.refresh_token,
  });

  const gmail = google.gmail({ version: 'v1', auth: oauth2Client });

  // Query emails from the last 7 days with financial keywords
  const res = await gmail.users.messages.list({
    userId: 'me',
    q: 'newer_than:7d ("spent" OR "debited" OR "charged" OR "paid" OR "payment" OR "transaction" OR "purchased")',
    maxResults: 50
  });

  const messages = res.data.messages || [];
  const fetchedEmails = [];

  for (const msg of messages) {
    if (!msg.id) continue;
    const msgData = await gmail.users.messages.get({ userId: 'me', id: msg.id });
    const payload = msgData.data.payload;
    if (!payload) continue;

    const headers = payload.headers || [];
    const subject = headers.find(h => h.name?.toLowerCase() === 'subject')?.value || '';
    const date = headers.find(h => h.name?.toLowerCase() === 'date')?.value || '';

    const body = decodeBody(payload);
    const plainText = stripHtml(body);

    fetchedEmails.push({ id: msg.id, subject, date, body: plainText });
  }

  return fetchedEmails;
}

function decodeBody(payload: any): string {
  const mimeType = payload.mimeType;
  const parts = payload.parts || [];
  const data = payload.body?.data;

  // 1. Handle single-part text
  if (data && mimeType === 'text/plain') {
    return Buffer.from(data, 'base64').toString('utf-8');
  }

  // 2. Handle single-part HTML
  if (data && mimeType === 'text/html') {
    return Buffer.from(data, 'base64').toString('utf-8');
  }

  // 3. Handle multipart (recursive)
  if (parts.length > 0) {
    // Priority 1: text/plain
    for (const part of parts) {
      if (part.mimeType === 'text/plain') {
        const res = decodeBody(part);
        if (res) return res;
      }
    }

    // Priority 2: text/html
    for (const part of parts) {
      if (part.mimeType === 'text/html') {
        const res = decodeBody(part);
        if (res) return res;
      }
    }

    // Priority 3: recurse into other multiparts
    for (const part of parts) {
      if (part.mimeType?.startsWith('multipart/')) {
        const res = decodeBody(part);
        if (res) return res;
      }
    }
  }

  return '';
}

function stripHtml(html: string): string {
  return html
    .replace(/<[^>]+>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}
