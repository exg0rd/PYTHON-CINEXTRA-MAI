import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import * as fc from 'fast-check'
import MovieCard from '../MovieCard'
import { MovieSummary } from '@/types/movie'

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

describe('Movie Navigation Property Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  /**
   * Feature: online-cinema, Property 7: Frontend Movie Detail Navigation
   * Validates: Requirements 3.2
   */
  it('should navigate to movie detail page when clicking on any movie in the list', () => {
    fc.assert(fc.property(
      fc.record({
        id: fc.integer({ min: 1, max: 10000 }),
        title: fc.string({ minLength: 1, maxLength: 100 }).filter(s => s.trim().length > 0),
        year: fc.integer({ min: 1900, max: 2030 }),
        genre: fc.constantFrom('Action', 'Comedy', 'Drama', 'Horror', 'Sci-Fi', 'Romance'),
        rating: fc.float({ min: 0.0, max: 10.0 }),
        poster_url: fc.option(fc.webUrl(), { nil: undefined })
      }),
      (movie: MovieSummary) => {
        render(<MovieCard movie={movie} />)

        // Find the movie card link
        const movieLink = screen.getByRole('link')
        
        // Verify the link points to the correct movie detail page
        expect(movieLink).toHaveAttribute('href', `/movies/${movie.id}`)
        
        // Verify the movie card contains the movie information
        expect(movieLink).toContainElement(screen.getByText(movie.title))
        expect(movieLink).toContainElement(screen.getByText(movie.year.toString()))
        expect(movieLink).toContainElement(screen.getByText(movie.genre))
        expect(movieLink).toContainElement(screen.getByText(movie.rating.toFixed(1)))
      }
    ), { numRuns: 100 })
  })
})