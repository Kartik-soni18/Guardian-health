export function generateSecurePassword(length = 12): string {
  const upper = 'ABCDEFGHJKLMNPQRSTUVWXYZ';
  const lower = 'abcdefghijkmnopqrstuvwxyz';
  const digits = '23456789';
  const special = '!@#$%&*';
  const all = upper + lower + digits + special;

  const pick = (chars: string) => chars[Math.floor(Math.random() * chars.length)];

  const required = [pick(upper), pick(lower), pick(digits), pick(special)];
  const remaining = Array.from({ length: Math.max(length - required.length, 4) }, () =>
    pick(all)
  );

  return [...required, ...remaining]
    .sort(() => Math.random() - 0.5)
    .join('');
}
