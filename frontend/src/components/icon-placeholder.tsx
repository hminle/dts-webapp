import {
  AlertCircleIcon,
  ArrowDownIcon,
  ArrowLeftIcon,
  ArrowLeftToLineIcon,
  ArrowRightIcon,
  ArrowRightToLineIcon,
  ArrowUpIcon,
  CheckIcon,
  ChevronDownIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  ChevronUpIcon,
  ChevronsUpDownIcon,
  CircleCheckIcon,
  CirclePlusIcon,
  CornerUpLeftIcon,
  CornerUpRightIcon,
  GripHorizontalIcon,
  GripVerticalIcon,
  InfoIcon,
  Loader2Icon,
  MinusIcon,
  MoreHorizontalIcon,
  OctagonXIcon,
  PanelLeftIcon,
  PinOffIcon,
  PlusIcon,
  SearchIcon,
  Settings2Icon,
  TriangleAlertIcon,
  XIcon,
} from "lucide-react"

/**
 * ReUI components are authored against a multi-icon-library placeholder so the
 * upstream docs site can swap icon packs. This app standardises on lucide, so the
 * shim just resolves the `lucide` name. Icons are imported by name to keep the
 * bundle tree-shakeable.
 */
const ICONS = {
  AlertCircleIcon,
  ArrowDownIcon,
  ArrowLeftIcon,
  ArrowLeftToLineIcon,
  ArrowRightIcon,
  ArrowRightToLineIcon,
  ArrowUpIcon,
  CheckIcon,
  ChevronDownIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  ChevronUpIcon,
  ChevronsUpDownIcon,
  CircleCheckIcon,
  CirclePlusIcon,
  CornerUpLeftIcon,
  CornerUpRightIcon,
  GripHorizontalIcon,
  GripVerticalIcon,
  InfoIcon,
  Loader2Icon,
  MinusIcon,
  MoreHorizontalIcon,
  OctagonXIcon,
  PanelLeftIcon,
  PinOffIcon,
  PlusIcon,
  SearchIcon,
  Settings2Icon,
  TriangleAlertIcon,
  XIcon,
} as const

type IconName = keyof typeof ICONS

export function IconPlaceholder({
  lucide,
  tabler: _tabler,
  hugeicons: _hugeicons,
  phosphor: _phosphor,
  remixicon: _remixicon,
  ...props
}: {
  lucide: string
  tabler?: string
  hugeicons?: string
  phosphor?: string
  remixicon?: string
} & React.ComponentProps<"svg">) {
  const Icon = ICONS[lucide as IconName]
  return Icon ? <Icon {...props} /> : null
}
