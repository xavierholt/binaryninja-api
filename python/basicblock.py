# Copyright (c) 2015-2016 Vector 35 LLC
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

import ctypes

# Binary Ninja components
import _binaryninjacore as core
import architecture
import highlight
import function


class BasicBlockEdge(object):
	def __init__(self, branch_type, target, arch):
		self.type = branch_type
		if self.type != core.BNBranchType.UnresolvedBranch:
			self.target = target
			self.arch = arch

	def __repr__(self):
		if self.type == core.BNBranchType.UnresolvedBranch:
			return "<%s>" % core.BNBranchType(self.type).name
		elif self.arch:
			return "<%s: %s@%#x>" % (self.type, self.arch.name, self.target)
		else:
			return "<%s: %#x>" % (self.type, self.target)


class BasicBlock(object):
	def __init__(self, view, handle):
		self.view = view
		self.handle = core.handle_of_type(handle, core.BNBasicBlock)

	def __del__(self):
		core.BNFreeBasicBlock(self.handle)

	@property
	def function(self):
		"""Basic block function (read-only)"""
		func = core.BNGetBasicBlockFunction(self.handle)
		if func is None:
			return None
		return function.Function(self.view, func)

	@property
	def arch(self):
		"""Basic block architecture (read-only)"""
		arch = core.BNGetBasicBlockArchitecture(self.handle)
		if arch is None:
			return None
		return architecture.Architecture(arch)

	@property
	def start(self):
		"""Basic block start (read-only)"""
		return core.BNGetBasicBlockStart(self.handle)

	@property
	def end(self):
		"""Basic block end (read-only)"""
		return core.BNGetBasicBlockEnd(self.handle)

	@property
	def length(self):
		"""Basic block length (read-only)"""
		return core.BNGetBasicBlockLength(self.handle)

	@property
	def outgoing_edges(self):
		"""List of basic block outgoing edges (read-only)"""
		count = ctypes.c_ulonglong(0)
		edges = core.BNGetBasicBlockOutgoingEdges(self.handle, count)
		result = []
		for i in xrange(0, count.value):
			branch_type = edges[i].type
			target = edges[i].target
			if edges[i].arch:
				arch = architecture.Architecture(edges[i].arch)
			else:
				arch = None
			result.append(BasicBlockEdge(branch_type, target, arch))
		core.BNFreeBasicBlockOutgoingEdgeList(edges)
		return result

	@property
	def has_undetermined_outgoing_edges(self):
		"""Whether basic block has undetermined outgoing edges (read-only)"""
		return core.BNBasicBlockHasUndeterminedOutgoingEdges(self.handle)

	@property
	def annotations(self):
		"""List of automatic annotations for the start of this block (read-only)"""
		return self.function.get_block_annotations(self.arch, self.start)

	@property
	def disassembly_text(self):
		return self.get_disassembly_text()

	@property
	def highlight(self):
		"""Highlight color for basic block"""
		color = core.BNGetBasicBlockHighlight(self.handle)
		if color.style == core.BNHighlightColorStyle.StandardHighlightColor:
			return highlight.HighlightColor(color=color.color, alpha=color.alpha)
		elif color.style == core.BNHighlightColorStyle.MixedHighlightColor:
			return highlight.HighlightColor(color=color.color, mix_color=color.mixColor, mix=color.mix, alpha=color.alpha)
		elif color.style == core.BNHighlightColorStyle.CustomHighlightColor:
			return highlight.HighlightColor(red=color.r, green=color.g, blue=color.b, alpha=color.alpha)
		return highlight.HighlightColor(color=core.BNHighlightStandardColor.NoHighlightColor)

	@highlight.setter
	def highlight(self, value):
		self.set_user_highlight(value)

	def __setattr__(self, name, value):
		try:
			object.__setattr__(self, name, value)
		except AttributeError:
			raise AttributeError("attribute '%s' is read only" % name)

	def __len__(self):
		return int(core.BNGetBasicBlockLength(self.handle))

	def __repr__(self):
		arch = self.arch
		if arch:
			return "<block: %s@%#x-%#x>" % (arch.name, self.start, self.end)
		else:
			return "<block: %#x-%#x>" % (self.start, self.end)

	def __iter__(self):
		start = self.start
		end = self.end

		idx = start
		while idx < end:
			data = self.view.read(idx, 16)
			inst_info = self.view.arch.get_instruction_info(data, idx)
			inst_text = self.view.arch.get_instruction_text(data, idx)

			yield inst_text
			idx += inst_info.length

	def mark_recent_use(self):
		core.BNMarkBasicBlockAsRecentlyUsed(self.handle)

	def get_disassembly_text(self, settings=None):
		settings_obj = None
		if settings:
			settings_obj = settings.handle

		count = ctypes.c_ulonglong()
		lines = core.BNGetBasicBlockDisassemblyText(self.handle, settings_obj, count)
		result = []
		for i in xrange(0, count.value):
			addr = lines[i].addr
			tokens = []
			for j in xrange(0, lines[i].count):
				token_type = core.BNInstructionTextTokenType(lines[i].tokens[j].type)
				text = lines[i].tokens[j].text
				value = lines[i].tokens[j].value
				size = lines[i].tokens[j].size
				operand = lines[i].tokens[j].operand
				tokens.append(function.InstructionTextToken(token_type, text, value, size, operand))
			result.append(function.DisassemblyTextLine(addr, tokens))
		core.BNFreeDisassemblyTextLines(lines, count.value)
		return result

	def set_auto_highlight(self, color):
		if not isinstance(color, highlight.HighlightColor):
			color = highlight.HighlightColor(color=color)
		core.BNSetAutoBasicBlockHighlight(self.handle, color._get_core_struct())

	def set_user_highlight(self, color):
		if not isinstance(color, highlight.HighlightColor):
			color = highlight.HighlightColor(color=color)
		core.BNSetUserBasicBlockHighlight(self.handle, color._get_core_struct())