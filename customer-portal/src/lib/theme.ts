import { call } from "./frappe-client"

export type ThemeTokens = {
  primaryColor: string
  primaryHover: string
  dangerColor: string
  dangerHover: string
  accentColor: string
  sidebarBg: string
  sidebarText: string
  sidebarActiveItemBg: string
  sidebarActiveText: string
  navbarBg: string
  navbarText: string
  navbarIcon: string
  pageHeadBg: string
  pageHeadText: string
  tableHeaderBg: string
  tableHeaderText: string
  tableEvenBg: string
  tableRowHoverBg: string
  selectRowHoverBg: string
  btnPrimaryBg: string
  btnPrimaryHover: string
  btnPrimaryText: string
  btnDangerBg: string
  btnDangerHover: string
}

const varMap: Record<keyof ThemeTokens, string> = {
  primaryColor: "--app-primary",
  primaryHover: "--app-primary-hover",
  dangerColor: "--app-danger",
  dangerHover: "--app-danger-hover",
  accentColor: "--app-accent-color",
  sidebarBg: "--app-sidebar-bg",
  sidebarText: "--app-sidebar-text",
  sidebarActiveItemBg: "--app-sidebar-active-bg",
  sidebarActiveText: "--app-sidebar-active-text",
  navbarBg: "--app-navbar-bg",
  navbarText: "--app-navbar-text",
  navbarIcon: "--app-navbar-icon",
  pageHeadBg: "--app-page-head-bg",
  pageHeadText: "--app-page-head-text",
  tableHeaderBg: "--app-table-header-bg",
  tableHeaderText: "--app-table-header-text",
  tableEvenBg: "--app-table-even-bg",
  tableRowHoverBg: "--app-table-row-hover-bg",
  selectRowHoverBg: "--app-select-row-hover-bg",
  btnPrimaryBg: "--app-btn-primary-bg",
  btnPrimaryHover: "--app-btn-primary-hover",
  btnPrimaryText: "--app-btn-primary-text",
  btnDangerBg: "--app-btn-danger-bg",
  btnDangerHover: "--app-btn-danger-hover",
}

export async function applyTheme() {
  try {
    const tokens = (await call.get("subamaz.api.get_theme")) as ThemeTokens
    const root = document.documentElement
    for (const [key, cssVar] of Object.entries(varMap)) {
      const val = tokens[key as keyof ThemeTokens]
      if (val) root.style.setProperty(cssVar, val)
    }
  } catch {
    // ignore
  }
}
