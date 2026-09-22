import './globals.css';

export const metadata = {
  title: 'BoxFinder',
  description: 'Jämför samlarkortsboxar efter pris, innehåll, odds och uppskattat värde.'
};

export default function RootLayout({ children }) {
  return <html lang="sv"><body>{children}</body></html>;
}
