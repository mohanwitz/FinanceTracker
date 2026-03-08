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

  // Query emails from the last 7 days
  const res = await gmail.users.messages.list({
    userId: 'me',
    q: 'newer_than:7d',
    maxResults: 20
  });

  const messages = res.data.messages || [];
  const fetchedEmails = [];

  for (const msg of messages) {
    if (!msg.id) continue;
    const msgData = await gmail.users.messages.get({ userId: 'me', id: msg.id });
    const payload = msgData.data.payload;
    const headers = payload?.headers || [];
    
    const subject = headers.find(h => h.name?.toLowerCase() === 'subject')?.value || '';
    const date = headers.find(h => h.name?.toLowerCase() === 'date')?.value || '';
    
    // Simplistic body extraction for MVP (base64 decode of parts)
    let body = '';
    if (payload?.parts) {
      const part = payload.parts.find(p => p.mimeType === 'text/plain');
      if (part?.body?.data) {
        body = Buffer.from(part.body.data, 'base64').toString('utf-8');
      }
    } else if (payload?.body?.data) {
      body = Buffer.from(payload.body.data, 'base64').toString('utf-8');
    }

    fetchedEmails.push({ id: msg.id, subject, date, body });
  }

  return fetchedEmails;
}