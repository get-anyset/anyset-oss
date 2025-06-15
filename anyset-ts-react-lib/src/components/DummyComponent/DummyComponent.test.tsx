import { render } from '@testing-library/react';

import { DummyComponent } from './DummyComponent';

describe('DummyComponent', () => {
  it('renders without crashing', () => {
    const app = render(<DummyComponent />);
    const element = app.getByText('Dummy Component');
    expect(element).toBeDefined();
  });

  it('matches snapshot', () => {
    const { asFragment } = render(<DummyComponent />);
    expect(asFragment()).toMatchSnapshot();
  });
});
