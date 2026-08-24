import { useCallback, useState } from 'react'

import { deleteDocument, listDocuments } from '../api'
import type { DocumentRecord } from '../types'

export function useDocuments() {
  const [documents, setDocuments] = useState<DocumentRecord[]>([])

  const refreshDocuments = useCallback(async () => {
    setDocuments(await listDocuments())
  }, [])

  const removeDocument = useCallback(async (documentId: string) => {
    await deleteDocument(documentId)
    await refreshDocuments()
  }, [refreshDocuments])

  return { documents, refreshDocuments, removeDocument }
}
