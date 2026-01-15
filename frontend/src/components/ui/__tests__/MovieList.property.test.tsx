import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import * as fc from 'fast-check'
import MovieList from '../MovieList'
import { MovieSummary } from '@/types/movie'

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

describe('MovieList Property Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  /**
   * Feature: online-cinema, Property 6: Frontend Movie List Display
   * Validates: Requirements 3.1
   */
  it('should display all movies with their basic information for any list of movies from the API', () => {
    fc.assert(fc.property(
      fc.array(fc.record({
        id: fc.integer({ min: 1, max: 10000 }),
        title: fc.string({ minLength: 1, maxLength: 100 }),
        year: fc.integer({ min: 1900, max: 2030 }),
        genre: fc.constantFrom('Action', 'Comedy', 'Drama', 'Horror', 'Sci-Fi', 'Romance'),
        rating: fc.float({ min: 0.0, max: 10.0 }),
        poster_url: fc.option(fc.webUrl(), { nil: undefined })
      }), { minLength: 1, maxLength: 20 }),
      (movies: MovieSummary[]) => {
        // Mock the hook to return our generated movies
        mockUseMovies.mockReturnValue({
          data: {
            movies,
            total: movies.length,
            page: 1,
            per_page: 20,
            total_pages: 1
          },
          loading: false,
          error: null,
          fetchMovies: vi.fn()
        })

        render(<MovieList />)

        // Verify all movies are displayed with their basic information
        movies.forEach(movie => {
          // Check that movie title is displayed
          expect(screen.getByText(movie.title)).toBeInTheDocument()
          
          // Check that movie year is displayed
          expect(screen.getByText(movie.year.toString())).toBeInTheDocument()
          
          // Check that movie genre is displayed
          expect(screen.getByText(movie.genre)).toBeInTheDocument()
          
          // Check that movie rating is displayed (formatted to 1 decimal place)
          expect(screen.getByText(movie.rating.toFixed(1))).toBeInTheDocument()
        })
      }
    ), { numRuns: 100 })
  })
})