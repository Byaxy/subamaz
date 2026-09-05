import { FrappeApp } from "frappe-js-sdk"

const siteUrl = import.meta.env.VITE_FRAPPE_SITE_URL || window.location.origin

export const frappeClient = new FrappeApp(siteUrl)
export const db = frappeClient.db()
export const call = frappeClient.call()
export const auth = frappeClient.auth()
export const file = frappeClient.file()
