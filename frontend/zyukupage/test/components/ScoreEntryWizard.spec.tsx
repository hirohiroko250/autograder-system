import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, beforeEach } from 'vitest';
import { ScoreEntryWizard } from '@/components/tests/score-entry-wizard';

// Test wrapper with providers
const TestWrapper = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('ScoreEntryWizard', () => {
  beforeEach(() => {
    // Reset any state between tests
  });

  it('renders the initial grade selection step', () => {
    render(
      <TestWrapper>
        <ScoreEntryWizard year="2025" period="summer" />
      </TestWrapper>
    );

    expect(screen.getByText('学年選択')).toBeInTheDocument();
    expect(screen.getByText('学年を選択してください')).toBeInTheDocument();
    expect(screen.getByText('1年生')).toBeInTheDocument();
    expect(screen.getByText('6年生')).toBeInTheDocument();
  });

  it('progresses through wizard steps correctly', async () => {
    render(
      <TestWrapper>
        <ScoreEntryWizard year="2025" period="summer" />
      </TestWrapper>
    );

    // Step 1: Select grade
    fireEvent.click(screen.getByText('6年生'));
    fireEvent.click(screen.getByText('次へ'));

    // Step 2: Select subject
    await waitFor(() => {
      expect(screen.getByText('教科選択')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('国語'));
    fireEvent.click(screen.getByText('次へ'));

    // Step 3: Select students
    await waitFor(() => {
      expect(screen.getByText('生徒選択')).toBeInTheDocument();
    });
    
    // Mock student selection
    const studentCheckboxes = screen.getAllByRole('button');
    fireEvent.click(studentCheckboxes[0]);
    fireEvent.click(screen.getByText('次へ'));

    // Step 4: Score entry
    await waitFor(() => {
      expect(screen.getByText('スコア入力')).toBeInTheDocument();
    });
  });

  it('validates required fields before allowing progression', () => {
    render(
      <TestWrapper>
        <ScoreEntryWizard year="2025" period="summer" />
      </TestWrapper>
    );

    // Try to proceed without selecting grade
    const nextButton = screen.getByText('次へ');
    expect(nextButton).toBeDisabled();

    // Select grade and verify button is enabled
    fireEvent.click(screen.getByText('6年生'));
    expect(nextButton).toBeEnabled();
  });

  it('shows progress indicator', () => {
    render(
      <TestWrapper>
        <ScoreEntryWizard year="2025" period="summer" />
      </TestWrapper>
    );

    expect(screen.getByText('Step 1 of 5')).toBeInTheDocument();
  });

  it('allows navigation back to previous steps', async () => {
    render(
      <TestWrapper>
        <ScoreEntryWizard year="2025" period="summer" />
      </TestWrapper>
    );

    // Go to step 2
    fireEvent.click(screen.getByText('6年生'));
    fireEvent.click(screen.getByText('次へ'));

    await waitFor(() => {
      expect(screen.getByText('教科選択')).toBeInTheDocument();
    });

    // Go back to step 1
    fireEvent.click(screen.getByText('戻る'));
    
    await waitFor(() => {
      expect(screen.getByText('学年選択')).toBeInTheDocument();
    });
  });

  it('handles Excel import functionality', async () => {
    render(
      <TestWrapper>
        <ScoreEntryWizard year="2025" period="summer" />
      </TestWrapper>
    );

    // Navigate to score entry step
    fireEvent.click(screen.getByText('6年生'));
    fireEvent.click(screen.getByText('次へ'));

    await waitFor(() => {
      fireEvent.click(screen.getByText('国語'));
      fireEvent.click(screen.getByText('次へ'));
    });

    await waitFor(() => {
      // Select a student
      const studentElements = screen.getAllByRole('button');
      fireEvent.click(studentElements[0]);
      fireEvent.click(screen.getByText('次へ'));
    });

    await waitFor(() => {
      const excelButton = screen.getByText('Excel取込');
      expect(excelButton).toBeInTheDocument();
      fireEvent.click(excelButton);
    });
  });
});