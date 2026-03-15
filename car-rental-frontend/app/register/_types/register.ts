export interface RegisterFormData {
  fullName: string;
  email: string;
  password: string;
  confirmPassword: string;
}

export interface PasswordRequirement {
  label: string;
  met: boolean;
}
