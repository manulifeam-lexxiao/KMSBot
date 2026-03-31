import "@testing-library/jest-dom";
import { vi } from "vitest";

// jsdom 不实现 scrollIntoView，全局 mock 避免 MessageList 测试报错
window.HTMLElement.prototype.scrollIntoView = vi.fn();
