import { describe, expect, it } from 'vitest'

import { hasMeaningfulCollectionChoice, uploadStatusKey } from './App'

describe('local workspace UX states', () => {
  it('only treats multiple collections as a meaningful choice', () => {
    expect(hasMeaningfulCollectionChoice([])).toBe(false)
    expect(hasMeaningfulCollectionChoice([{ id: 'default' } as never])).toBe(false)
    expect(hasMeaningfulCollectionChoice([{ id: 'default' } as never, { id: 'work' } as never])).toBe(true)
  })

  it('represents each upload state without claiming progress', () => {
    expect(uploadStatusKey('idle')).toBeNull()
    expect(uploadStatusKey('selected')).toBe('selected')
    expect(uploadStatusKey('uploading')).toBe('uploading')
    expect(uploadStatusKey('ready')).toBe('ready')
    expect(uploadStatusKey('error')).toBe('error')
  })
})
