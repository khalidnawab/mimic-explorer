import { useState, useEffect } from 'react'
import { api } from '../../api/client'
import Badge from '../common/Badge'

interface NotesTabProps {
  hadmId: number
}

export default function NotesTab({ hadmId }: NotesTabProps) {
  const [notes, setNotes] = useState<any[]>([])
  const [expandedId, setExpandedId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    api.getEncounterNotes(hadmId)
      .then((data) => {
        setNotes(data.results || data)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [hadmId])

  if (loading) return <div className="animate-pulse h-32 bg-gray-100 rounded" />
  if (notes.length === 0) return <p className="text-gray-500 text-sm py-4">No notes for this encounter</p>

  return (
    <div className="space-y-3">
      {notes.map((note: any) => {
        const isExpanded = expandedId === note.id
        return (
          <div key={note.id} className="border border-gray-200 rounded-lg overflow-hidden">
            <button
              onClick={() => setExpandedId(isExpanded ? null : note.id)}
              className="w-full flex items-center justify-between px-4 py-3 bg-gray-50 hover:bg-gray-100 transition-colors text-left"
            >
              <div className="flex items-center gap-3">
                <Badge label={note.note_type || 'Note'} variant="info" />
                <span className="text-sm text-gray-500">
                  {note.charttime ? formatDate(note.charttime) : 'No date'}
                </span>
              </div>
              <span className="text-gray-400 text-sm">{isExpanded ? '\u25B2' : '\u25BC'}</span>
            </button>
            {isExpanded && (
              <div className="px-4 py-3 bg-white">
                <pre className="text-sm text-gray-700 whitespace-pre-wrap font-sans leading-relaxed">
                  {note.text || 'No content'}
                </pre>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}
