export type UserRole = "admin" | "manager" | "user";

export type Profile = {
  id: number;
  user_id: number;
  name: string | null;
  phone: string | null;
  address: string | null;
};

export type AuthMe = {
  email: string;
  role: UserRole;
  profile: Profile;
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
};

export type FieldErrors = Record<string, string>;
