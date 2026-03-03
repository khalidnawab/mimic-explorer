import { useState, ReactNode } from 'react'

export interface Tab {
  key: string
  label: string
  content: ReactNode
  hidden?: boolean
}

interface TabsProps {
  tabs: Tab[]
  defaultTab?: string
}

export default function Tabs({ tabs, defaultTab }: TabsProps) {
  const visibleTabs = tabs.filter((t) => !t.hidden)
  const [activeKey, setActiveKey] = useState(defaultTab || visibleTabs[0]?.key || '')

  const activeTab = visibleTabs.find((t) => t.key === activeKey)

  return (
    <div>
      <div className="border-b border-gray-200">
        <nav className="flex gap-0 -mb-px">
          {visibleTabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveKey(tab.key)}
              className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                activeKey === tab.key
                  ? 'border-primary-600 text-primary-700'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>
      <div className="pt-4">{activeTab?.content}</div>
    </div>
  )
}
