/**
 * Database types for Supabase tables
 * Based on deploy/sql/001_initial_schema.sql
 */

// ============================================
// CORE TYPES
// ============================================

export interface Post {
  id: string;
  url: string;
  author_handle: string | null;
  author_name: string | null;
  content: string | null;
  posted_at: string | null;
  archived_at: string;
  archived_via: string;
  tags: string[] | null;
  topics: string[] | null;
  notes: string | null;
  importance: string | null;
  thread_position: number | null;
  is_thread: boolean;
  quoted_post_id: string | null;
  quoted_text: string | null;
  quoted_author: string | null;
  quoted_url: string | null;
  embedding: number[] | null;
}

export interface PostMedia {
  id: number;
  post_id: string;
  type: string | null;
  url: string | null;
  category: "text_heavy" | "chart" | "general" | null;
  description: string | null;
  extracted_at: string | null;
  extraction_model: string | null;
}

// ============================================
// THESIS SYSTEM TYPES
// ============================================

export interface EntityCategory {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
}

export interface Entity {
  id: string;
  name: string;
  category_id: string | null;
  description: string | null;
  aliases: string[];
  embedding: number[] | null;
  created_at: string;
}

export interface Thesis {
  id: string;
  name: string;
  category: "investing" | "health" | "tech" | string | null;
  description: string | null;
  current_synthesis: string | null;
  synthesis_updated_at: string | null;
  synthesis_post_count: number;
  embedding: number[] | null;
  created_at: string;
}

// ============================================
// JUNCTION TABLE TYPES
// ============================================

export interface PostEntity {
  post_id: string;
  entity_id: string;
  confidence: number;
  manually_verified: boolean;
}

export interface PostThesis {
  post_id: string;
  thesis_id: string;
  contribution: string | null;
  confidence: number;
  manually_verified: boolean;
}

export interface EntityThesis {
  entity_id: string;
  thesis_id: string;
  role: string;
}

export interface ThesisRelationship {
  thesis_a_id: string;
  thesis_b_id: string;
  relationship_type: string | null;
  description: string | null;
}

// ============================================
// SESSION TYPES
// ============================================

export interface Session {
  id: string;
  name: string | null;
  created_at: string;
  updated_at: string;
  conversation: unknown; // JSONB
}

export interface SessionPost {
  session_id: string;
  post_id: string;
  added_at: string;
}

// ============================================
// ENRICHED TYPES (with relations)
// ============================================

export interface PostWithMedia extends Post {
  post_media: PostMedia[];
}

export interface PostWithRelations extends Post {
  post_media: PostMedia[];
  post_entities: Array<{
    entity: Entity & { category: EntityCategory | null };
    confidence: number;
  }>;
  post_theses: Array<{
    thesis: Thesis;
    contribution: string | null;
    confidence: number;
  }>;
}

export interface EntityWithCategory extends Entity {
  category: EntityCategory | null;
}

export interface EntityWithRelations extends Entity {
  category: EntityCategory | null;
  post_entities: Array<{ post: Post }>;
  entity_theses: Array<{ thesis: Thesis; role: string }>;
}

export interface ThesisWithRelations extends Thesis {
  post_theses: Array<{
    post: Post;
    contribution: string | null;
  }>;
  entity_theses: Array<{
    entity: Entity & { category: EntityCategory | null };
    role: string;
  }>;
  related_theses: Array<{
    thesis: Thesis;
    relationship_type: string | null;
  }>;
}

// ============================================
// SEARCH RESULT TYPES
// ============================================

export interface SearchResult extends PostWithRelations {
  similarity: number;
}

// ============================================
// STATS TYPE
// ============================================

export interface Stats {
  total_posts: number;
  total_entities: number;
  total_theses: number;
  unique_authors: number;
}

// ============================================
// DATABASE TYPE (for Supabase client typing)
// ============================================

export interface Database {
  public: {
    Tables: {
      posts: {
        Row: Post;
        Insert: Omit<Post, "archived_at"> & { archived_at?: string };
        Update: Partial<Post>;
      };
      post_media: {
        Row: PostMedia;
        Insert: Omit<PostMedia, "id">;
        Update: Partial<PostMedia>;
      };
      entity_categories: {
        Row: EntityCategory;
        Insert: Omit<EntityCategory, "id" | "created_at">;
        Update: Partial<EntityCategory>;
      };
      entities: {
        Row: Entity;
        Insert: Omit<Entity, "id" | "created_at">;
        Update: Partial<Entity>;
      };
      theses: {
        Row: Thesis;
        Insert: Omit<Thesis, "id" | "created_at">;
        Update: Partial<Thesis>;
      };
      post_entities: {
        Row: PostEntity;
        Insert: PostEntity;
        Update: Partial<PostEntity>;
      };
      post_theses: {
        Row: PostThesis;
        Insert: PostThesis;
        Update: Partial<PostThesis>;
      };
      entity_theses: {
        Row: EntityThesis;
        Insert: EntityThesis;
        Update: Partial<EntityThesis>;
      };
      thesis_relationships: {
        Row: ThesisRelationship;
        Insert: ThesisRelationship;
        Update: Partial<ThesisRelationship>;
      };
      sessions: {
        Row: Session;
        Insert: Omit<Session, "id" | "created_at" | "updated_at">;
        Update: Partial<Session>;
      };
      session_posts: {
        Row: SessionPost;
        Insert: Omit<SessionPost, "added_at">;
        Update: Partial<SessionPost>;
      };
    };
    Functions: {
      match_posts: {
        Args: {
          query_embedding: number[];
          match_threshold?: number;
          match_count?: number;
        };
        Returns: Array<{
          id: string;
          content: string;
          similarity: number;
        }>;
      };
    };
  };
}
