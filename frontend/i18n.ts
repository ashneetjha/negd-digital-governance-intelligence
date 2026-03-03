import { getRequestConfig } from "next-intl/server";

const SUPPORTED_LOCALES = new Set(["en", "hi"]);

export default getRequestConfig(async ({ requestLocale }) => {
    const resolvedLocale = await requestLocale;
    const locale = resolvedLocale && SUPPORTED_LOCALES.has(resolvedLocale) ? resolvedLocale : "en";

    return {
        locale,
        messages: (await import(`./messages/${locale}.json`)).default,
    };
});
