#pragma once

#include <QtWidgets/QDialog>
#include <QtWidgets/QLabel>
#include <QtCore/QStringListModel>
#include <QtWidgets/QComboBox>
#include <QtCore/QTimer>
#include <QtCore/QThread>
#include "binaryninjaapi.h"
#include "dialogtextedit.h"

class BINARYNINJAUIAPI PossibleValueSetDialog: public QDialog
{
	Q_OBJECT

	QComboBox* m_combo;
	DialogTextEdit* m_value;
	QStringListModel* m_model;
	QLabel* m_prompt;
	QString m_promptText;
	BinaryViewRef m_view;
	bool m_resultValid;
	QStringList m_historyEntries;
	int m_historySize;
	QFont m_defaultFont;
	bool m_initialTextSelection;
	BinaryNinja::PossibleValueSet m_valueSet;
	QPushButton* m_acceptButton;
	QPalette m_defaultPalette;
	QString m_parseError;
	uint64_t m_here;
	QTimer* m_updateTimer;

private Q_SLOTS:
	void accepted();
	void checkParse();
	void updateTimerEvent();

public:
	PossibleValueSetDialog(QWidget* parent, BinaryViewRef view, uint64_t here);
	BinaryNinja::PossibleValueSet getPossibleValueSet() const { return m_valueSet; }
};

static const QStringList valueSets = {
	"Undetermined",
	"ConstantValue",
	"ConstantPointerValue",
	"StackFrameOffset",
	"SignedRangeValue",
	"UnsignedRangeValue",
	"InSetOfValues",
	"NotInSetOfValues"
	// "LookupTableValue" - currently unsupported
};
