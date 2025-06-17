# Documentation

This directory contains all project documentation organized by category for easy navigation and maintenance.

## Directory Structure

```
docs/
├── README.md              # This file - documentation overview
├── adr/                   # Architecture Decision Records
├── development/           # Developer documentation
├── releases/              # Release notes and version history
└── security/              # Security documentation
```

## Documentation Categories

### Architecture Decision Records (ADR)
**Location**: `docs/adr/`

Contains records of significant architectural decisions made during the project lifecycle. ADRs document the context, decision, and consequences of important technical choices.

### Development Documentation
**Location**: `docs/development/`

- [Developer's Guide](development/DEVELOPER_GUIDE.md) - Complete guide for creating custom plugins

### Release Documentation
**Location**: `docs/releases/`

- [Release Notes](releases/RELEASE_NOTES.md) - Detailed history of changes and improvements
- Version tags (TAG_v*.md) - Individual release documentation

### Security Documentation
**Location**: `docs/security/`

- [Security Setup](security/SECURITY_SETUP.md) - Security configuration and best practices

## Contributing to Documentation

When adding new documentation:

1. **Choose the appropriate category** based on the content type
2. **Follow existing naming conventions** within each directory
3. **Update relevant cross-references** when moving or renaming files
4. **Keep this overview file updated** when adding new major documentation sections

## Cross-References

Key documentation files are referenced throughout the project:

- Root [README.md](../README.md) links to developer guide and release notes
- Plugin READMEs link to release notes for version history
- Installation scripts reference security documentation

When updating file paths, ensure all cross-references are maintained.

## Documentation Standards

- Use Markdown format for all documentation
- Include table of contents for longer documents
- Use relative links for internal references
- Follow consistent heading hierarchy
- Include code examples where applicable
- Keep documentation current with code changes

## Maintenance

This documentation structure supports:

- **Easier navigation** - logical grouping by purpose
- **Better maintenance** - clear ownership and organization
- **Version control** - separate directories for different concerns
- **Future growth** - extensible structure for new documentation types
