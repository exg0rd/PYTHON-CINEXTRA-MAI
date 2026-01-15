import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import * as fc from 'fast-check'
import MovieList from '../MovieList'

// Mock the useMovies hook
vi.mock('@/hooks/useMovies', () => ({
  useMovies: vi.fn()
}))

// Mock Next.js components
vi.mock('next/link', () => ({
  default: ({ children, href, ...props }: any) => (
    <a href={href} {...props}>{children}</a>
  )
}))

vi.mock('next/image', () => ({
  default: ({ src, alt, ...props }: any) => (
    <img src={src} alt={alt} {...props} />
  )
}))

import { useMovies } from '@/hooks/useMovies'

const mockUseMovies = useMovies as any

describe('Loading State Property Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  /**
   * Feature: online-cinema, Property 8: Frontend Loading State Management
   * Validates: Requirements 3.4
   */
  it('should display loading states during API requests and clear them upon completion', () => {
    fc.assert(fc.property(
      fc.boolean(), // loading state
      fc.option(fc.array(fc.record({
        id: fc.integer({ min: 1, max: 10000 }),
        title: fc.string({ minLength: 1, maxLength: 100 }),
        year: fc.integer({ min: 1900, max: 2030 }),
        genre: fc.constantFrom('Action', 'Comedy', 'Drama', 'Horror', 'Sci-Fi', 'Romance'),
        rating: fc.float({ min: 0.0, max: 10.0 }),
        poster_url: fc.option(fc.webUrl(), { nil: undefined })
      }), { minLength: 0, maxLength: 20 }), { nil: null }), // data (can be null during loading)
      (loading, data) => {
        // Mock the hook to return the loading state and data
        mockUseMovies.mockReturnValue({
          data: data ? {
            movies: data,
            total: data.length,
            page: 1,
            per_page: 20,
            total_pages: 1
          } : null,
          loading,
          error: null,
          fetchMovies: vi.fn()
        })

        render(<MovieList />)

        if (loading && !data) {
          // When loading and no data, should show skeleton components
          const skeletons = screen.getAllByRole('generic').filter(el => 
            el.className.includes('animate-pulse')
          )
          expect(skeletons.length).toBeGreaterThan(0)
        } else if (loading && data) {
          // When loading with existing data, should show loading spinner
          const loadingSpinner = screen.getByRole('generic', { 
            name: /loading/i 
          }) || document.querySelector('.animate-spin')
          expect(loadingSpinner).toBeTruthy()
        } else if (!loading && data) {
          // When not loading and has data, should not show loading indicators
          const skeletons = screen.queryAllByRole('generic').filter(el => 
            el.className.includes('animate-pulse')
          )
          const spinners = document.querySelectorAll('.animate-spin')
          expect(skeletons.length).toBe(0)
          expect(spinners.length).toBe(0)
        }
      }
    ), { numRuns: 100 })
  })
})