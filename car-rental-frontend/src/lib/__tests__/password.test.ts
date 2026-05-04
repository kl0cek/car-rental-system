import { getPasswordRequirements, isPasswordValid } from '@/lib/password';

describe('getPasswordRequirements', () => {
  it('flags too short password', () => {
    const reqs = getPasswordRequirements('Ab1');
    expect(reqs.find((r) => r.label === 'pwd.min8')?.met).toBe(false);
  });

  it('flags missing digit', () => {
    const reqs = getPasswordRequirements('Abcdefgh');
    expect(reqs.find((r) => r.label === 'pwd.number')?.met).toBe(false);
  });

  it('flags missing uppercase', () => {
    const reqs = getPasswordRequirements('abcdefg1');
    expect(reqs.find((r) => r.label === 'pwd.uppercase')?.met).toBe(false);
  });

  it('all requirements met for valid password', () => {
    const reqs = getPasswordRequirements('Abcdefg1');
    expect(reqs.every((r) => r.met)).toBe(true);
  });
});

describe('isPasswordValid', () => {
  it.each([
    ['empty', '', false],
    ['too short', 'Ab1', false],
    ['no digit', 'Abcdefgh', false],
    ['no uppercase', 'abcdefg1', false],
    ['valid 8 chars', 'Abcdefg1', true],
    ['valid long', 'SuperSecret123', true],
  ])('%s -> %s', (_label, password, expected) => {
    expect(isPasswordValid(password)).toBe(expected);
  });
});
