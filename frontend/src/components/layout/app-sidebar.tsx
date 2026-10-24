import { useLocation } from '@tanstack/react-router'
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarRail,
} from '@/components/ui/sidebar'
import { DataDisclaimer } from '@/components/data-disclaimer'
import { AppTitle } from './app-title'
import { FOOTER_ITEMS, MENU_ITEMS } from './data/sidebar-data'
import { NavGroup, SidebarMenuLink } from './nav-group'

export function AppSidebar() {
  const href = useLocation({ select: (location) => location.href })

  return (
    // A landmark, so screen-reader users can jump to the menu; on phones the
    // sidebar is a sheet (a dialog) and Sidebar doesn't pass these through.
    <Sidebar
      collapsible='icon'
      variant='inset'
      role='navigation'
      aria-label='Main'
    >
      <SidebarHeader>
        <AppTitle />
      </SidebarHeader>
      <SidebarContent>
        <NavGroup title='Analysis' items={MENU_ITEMS} />
      </SidebarContent>
      <SidebarFooter>
        <SidebarMenu>
          {FOOTER_ITEMS.map((item) => (
            <SidebarMenuLink key={item.title} item={item} href={href} />
          ))}
        </SidebarMenu>
        <DataDisclaimer />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}
