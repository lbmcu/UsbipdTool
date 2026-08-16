# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-08-16

### Added

- Detect `usbipd` at startup, with install guidance when missing.
- Scan USB devices via `usbipd state` (JSON), falling back to `usbipd list`.
- Context-aware actions: bind (with `--force`), unbind, attach to WSL, detach.
- Attach dialog with WSL distro picker, optional `--host-ip`, and `--auto-attach`.
- Live log panel echoing the exact `usbipd` commands and output.
- English / 简体中文 UI switching.
- Light / dark / follow-system theme switching.
- Persistent settings in `%APPDATA%\UsbipdTool\config.json`.
- Single-file, windowed, UAC-elevated EXE via PyInstaller.
- GitHub Actions workflow to build the EXE on PR and publish releases on tags.
