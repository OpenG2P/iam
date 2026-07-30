import type { Metadata } from "next";
import "@/app/globals.css";
import { NextIntlClientProvider } from "next-intl";
import { getMessages } from "next-intl/server";
import { Roboto, Roboto_Slab } from "next/font/google";
import { getServerEnv } from "@/app/api/_lib/env-config";
import { AuthProvider } from "@/context/Authcontext";
import { ConfigProvider } from "@/context/ConfigContext";
import { RbacProvider } from "@/context/RbacContext";
import Layout from "@/components/Layout";
import { ToastContainer } from "react-toastify";
import 'react-toastify/dist/ReactToastify.css';

const roboto = Roboto({
  weight: ["300", "400", "500", "700"],
  style: ["normal"],
  subsets: ["latin"],
  display: "swap",
  variable: "--font-roboto",
});

const robotoSlab = Roboto_Slab({
  weight: ["300", "400", "500", "700"],
  style: ["normal"],
  subsets: ["latin"],
  display: "swap",
  variable: "--font-roboto-slab",
});

export const metadata: Metadata = {
  title: "Identity & Access Management",
  description: "OpenG2P IAM Staff Admin",
  icons: {
    icon: "/favicon.svg",
  },
};

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const messages = await getMessages();
  const { pageSize } = getServerEnv();

  return (
    <html lang={locale}>
      <body className={`${roboto.variable} ${robotoSlab.variable}`}>
        <NextIntlClientProvider messages={messages}>
          <ConfigProvider pageSize={pageSize}>
            <AuthProvider>
              <RbacProvider>
                <Layout>{children}</Layout>
                <ToastContainer position="top-right" autoClose={5000} hideProgressBar={false} newestOnTop closeOnClick rtl={false} pauseOnFocusLoss draggable pauseOnHover />
              </RbacProvider>
            </AuthProvider>
          </ConfigProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
